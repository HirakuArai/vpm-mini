#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_TIMEOUT_SEC = 300
MAX_OPENAI_RETRIES = 3


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def strip_code_fences(text: str) -> str:
    lines = text.strip()
    if lines.startswith("```"):
        lines = lines.lstrip("`")
        parts = lines.split("\n", 1)
        if len(parts) == 2:
            lines = parts[1]
    if lines.endswith("```"):
        lines = lines[:-3].rstrip()
    return lines


def get_openai_base_url() -> str:
    base = os.getenv("OPENAI_BASE_URL", "").strip()
    if not base:
        base = DEFAULT_OPENAI_BASE_URL
    base = base.rstrip("/")
    if not base.startswith("http"):
        raise RuntimeError(f"Invalid OPENAI_BASE_URL: {base!r}")
    return base


def get_openai_timeout_sec() -> float:
    raw = os.getenv("OPENAI_TIMEOUT_SEC", "").strip()
    if not raw:
        return float(DEFAULT_OPENAI_TIMEOUT_SEC)
    try:
        value = float(raw)
    except ValueError as exc:  # noqa: BLE001
        raise RuntimeError(f"Invalid OPENAI_TIMEOUT_SEC: {raw!r}") from exc
    if value <= 0:
        raise RuntimeError(f"Invalid OPENAI_TIMEOUT_SEC (must be >0): {raw!r}")
    return value


def call_openai(
    api_key: str, messages: List[Dict[str, str]], model: str, base_url: str
) -> str:
    url = f"{base_url}/chat/completions"
    timeout_sec = get_openai_timeout_sec()
    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    backoff = {1: 1, 2: 3}
    last_err: Exception | None = None

    for attempt in range(1, MAX_OPENAI_RETRIES + 1):
        req = Request(url, data=data, headers=headers)
        try:
            with urlopen(req, timeout=timeout_sec) as resp:
                body = resp.read().decode("utf-8")
            content = json.loads(body)["choices"][0]["message"]["content"]
            return content
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            status = getattr(exc, "code", None)
            retriable = status is not None and 500 <= int(status) < 600
            last_err = RuntimeError(
                f"OpenAI HTTPError (model={model}, attempt={attempt}/{MAX_OPENAI_RETRIES}, timeout={timeout_sec}s): {status} {detail}"
            )
        except socket.timeout as exc:
            retriable = True
            last_err = RuntimeError(
                f"OpenAI timeout (model={model}, attempt={attempt}/{MAX_OPENAI_RETRIES}, timeout={timeout_sec}s): {exc}"
            )
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            reason_text = str(reason)
            retriable = (
                "Remote end closed" in reason_text
                or "Connection reset" in reason_text
                or isinstance(reason, socket.timeout)
            )
            last_err = RuntimeError(
                f"OpenAI URLError (model={model}, attempt={attempt}/{MAX_OPENAI_RETRIES}, timeout={timeout_sec}s): {reason_text}"
            )
        except Exception as exc:  # noqa: BLE001
            retriable = False
            last_err = RuntimeError(
                f"Unexpected OpenAI response (model={model}, attempt={attempt}/{MAX_OPENAI_RETRIES}): {exc}"
            )

        if not retriable or attempt == MAX_OPENAI_RETRIES:
            assert last_err is not None
            raise last_err

        sleep_sec = backoff.get(attempt, 10)
        print(
            f"Warn: OpenAI call failed (attempt={attempt}/{MAX_OPENAI_RETRIES}, retry in {sleep_sec}s): {last_err}",
            file=sys.stderr,
        )
        time.sleep(sleep_sec)

    assert last_err is not None
    raise last_err


def truncate(text: str, limit: int = 320) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def summarize_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    summarized = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        if not nid:
            continue
        if n.get("kind") != "decision":
            continue
        summarized.append(
            {
                "id": nid,
                "title": n.get("title", ""),
                "summary": truncate(n.get("summary", "") or ""),
                "scope_file": (
                    n.get("scope", {}).get("file", "")
                    if isinstance(n.get("scope"), dict)
                    else ""
                ),
            }
        )
    return summarized


def build_messages(
    project_id: str, snapshot_name: str, model: str, new_decisions, old_decisions
):
    system = textwrap.dedent(
        """
        You are PM Kai acting as a mediator. Propose supersedes candidates between new decisions (from a snapshot) and existing decisions (canonical).
        Output MUST be pure JSON (no Markdown, no code fences) with keys:
        - project_id, snapshot, model, generated_at, suggestions, questions
        suggestions: list of {{ new, old:[...], confidence:0-1, rationale }}
        questions: list of {{ about_new, question, options }}
        If unsure, keep confidence low and add a question instead of forcing supersedes.
        """
    ).strip()

    def format_list(title: str, items: List[Dict[str, str]]) -> str:
        if not items:
            return f"{title}: none\n"
        lines = [f"{title} (count={len(items)}):"]
        for i in items:
            lines.append(
                f"- id={i.get('id')} | title={i.get('title','')} | summary={i.get('summary','')} | scope_file={i.get('scope_file','')}"
            )
        return "\n".join(lines)

    user = "\n\n".join(
        [
            f"project_id={project_id}",
            f"snapshot={snapshot_name}",
            f"model={model}",
            format_list("new decisions (snapshot)", new_decisions),
            format_list("existing decisions (canonical)", old_decisions),
            "Instructions:\n- For each new decision, propose zero or more old decision ids it likely supersedes.\n- If no good match, leave old=[].\n- Add a short rationale.\n- If uncertain, add a question for the owner in the questions list.",
        ]
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--canonical-nodes",
        default="data/hakone-e2/info_nodes_v1.json",
        help="Path to canonical info_nodes JSON",
    )
    ap.add_argument(
        "--canonical-relations",
        default="data/hakone-e2/info_relations_v1.json",
        help="Path to canonical info_relations JSON (unused in v1.0)",
    )
    ap.add_argument(
        "--snapshot",
        required=True,
        help="Snapshot JSON (expects aya_output.info_nodes/info_relations)",
    )
    ap.add_argument("--model", default="gpt-4.1")
    ap.add_argument(
        "--output",
        required=True,
        help="Where to write suggestions JSON",
    )
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required")

    base_url = get_openai_base_url()
    model = args.model
    snapshot_path = Path(args.snapshot)
    snapshot_name = snapshot_path.name

    canonical_nodes = load_json(Path(args.canonical_nodes), [])
    snapshot = load_json(snapshot_path, {})
    aya = snapshot.get("aya_output", {}) if isinstance(snapshot, dict) else {}
    snapshot_nodes = aya.get("info_nodes", []) or []

    new_decisions = summarize_nodes(snapshot_nodes)
    old_decisions = summarize_nodes(canonical_nodes)

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    if not new_decisions or not old_decisions:
        out = {
            "project_id": "hakone-e2",
            "snapshot": snapshot_name,
            "model": model,
            "generated_at": generated_at,
            "suggestions": [],
            "questions": [],
            "notes": "No decision nodes available; nothing to suggest.",
        }
        save_json(Path(args.output), out)
        print("No decisions found; wrote empty suggestions.")
        return

    messages = build_messages(
        "hakone-e2", snapshot_name, model, new_decisions, old_decisions
    )
    content = call_openai(api_key, messages, model, base_url)
    content = strip_code_fences(content)
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to parse model response as JSON: {exc}")

    # Ensure required metadata
    payload.setdefault("project_id", "hakone-e2")
    payload.setdefault("snapshot", snapshot_name)
    payload.setdefault("model", model)
    payload.setdefault("generated_at", generated_at)
    payload.setdefault("suggestions", [])
    payload.setdefault("questions", [])

    save_json(Path(args.output), payload)
    print(
        f"Suggestions written to {args.output} "
        f"(new decisions={len(new_decisions)}, existing decisions={len(old_decisions)})"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
