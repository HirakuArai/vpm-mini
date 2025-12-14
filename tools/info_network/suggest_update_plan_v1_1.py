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


# -------------------------------
# File helpers
# -------------------------------
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


# -------------------------------
# Normalization (borrowed from v0.1 generator)
# -------------------------------
def normalize_source_refs(val: Any) -> Any:
    if not isinstance(val, list):
        return val
    refs = [r for r in val if isinstance(r, dict)]
    return sorted(refs, key=lambda r: (r.get("kind", ""), r.get("value", "")))


def normalize_list(val: Any) -> Any:
    if not isinstance(val, list):
        return val
    try:
        return sorted(val)
    except Exception:
        return val


def normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in node.items():
        if k in {"updated_at", "created_at"}:
            continue
        out[k] = v
    if "source_refs" in out:
        out["source_refs"] = normalize_source_refs(out["source_refs"])
    for k in ("tags", "hints"):
        if k in out:
            out[k] = normalize_list(out[k])
    return out


def normalize_relation(rel: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in rel.items():
        if k in {"updated_at", "created_at"}:
            continue
        out[k] = v
    if "source_refs" in out:
        out["source_refs"] = normalize_source_refs(out["source_refs"])
    return out


def seed_plan_from_snapshot(
    canonical_nodes: List[Dict[str, Any]],
    canonical_rels: List[Dict[str, Any]],
    snap_nodes: List[Dict[str, Any]],
    snap_rels: List[Dict[str, Any]],
    snapshot_name: str,
) -> Dict[str, Any]:
    cn = {
        n.get("id"): n for n in canonical_nodes if isinstance(n, dict) and n.get("id")
    }
    cr = {r.get("id"): r for r in canonical_rels if isinstance(r, dict) and r.get("id")}

    add: List[Dict[str, Any]] = []
    update: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    noop_nodes: List[str] = []

    for n in snap_nodes:
        nid = n.get("id")
        if not nid:
            continue
        if nid in cn:
            if normalize_node(cn[nid]) == normalize_node(n):
                noop_nodes.append(nid)
            else:
                update.append(n)
            matches.append({"new": nid, "existing": [nid]})
        else:
            add.append(n)
            matches.append({"new": nid, "existing": []})

    add_rels: List[Dict[str, Any]] = []
    update_rels: List[Dict[str, Any]] = []
    noop_rels: List[str] = []

    for r in snap_rels:
        rid = r.get("id")
        if not rid:
            continue
        if rid in cr:
            if normalize_relation(cr[rid]) == normalize_relation(r):
                noop_rels.append(rid)
            else:
                update_rels.append(r)
        else:
            add_rels.append(r)

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "project_id": "hakone-e2",
        "source_snapshot_id": snapshot_name,
        "generated_at": now,
        "matches": matches,
        "add": add,
        "add_relations": add_rels,
        "update": update,
        "update_relations": update_rels,
        "obsolete": [],
        "obsolete_relations": [],
        "supersedes": [],
        "notes": "seed plan (v0.1 rule): id-based add/update with no-op detection; no semantic judgment.",
        "noop": noop_nodes,
        "noop_relations": noop_rels,
    }


# -------------------------------
# OpenAI helpers
# -------------------------------
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


# -------------------------------
# Prompt helpers
# -------------------------------
def truncate(text: str, limit: int = 320) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def summarize_decisions(nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        if n.get("kind") != "decision":
            continue
        nid = n.get("id")
        if not nid:
            continue
        out.append(
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
    return out


def build_messages(
    project_id: str,
    snapshot_name: str,
    model: str,
    seed_plan: Dict[str, Any],
    canonical_decisions: List[Dict[str, str]],
    snapshot_decisions: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    seed_summary = textwrap.dedent(
        f"""
        Seed plan (mechanical v0.1):
        - add: {len(seed_plan.get('add', []))} nodes, add_relations: {len(seed_plan.get('add_relations', []))}
        - update: {len(seed_plan.get('update', []))} nodes, update_relations: {len(seed_plan.get('update_relations', []))}
        - noop: {len(seed_plan.get('noop', []))} nodes, noop_relations: {len(seed_plan.get('noop_relations', []))}
        """
    ).strip()

    def format_decisions(title: str, items: List[Dict[str, str]]) -> str:
        if not items:
            return f"{title}: none\n"
        lines = [f"{title} (count={len(items)}):"]
        for i in items:
            lines.append(
                f"- id={i.get('id')} | title={i.get('title','')} | summary={i.get('summary','')} | scope_file={i.get('scope_file','')}"
            )
        return "\n".join(lines)

    system = textwrap.dedent(
        """
        You are PM Kai proposing an info_update_plan_v1.1. Output MUST be pure JSON (no Markdown, no code fences).
        Your job: suggest only the semantic parts (obsolete, supersedes, questions). Do NOT change add/update/add_relations/update_relations from the seed.
        Be safe: if unsure, leave supersedes/obsolete empty and add a question for the owner.
        Output keys:
        project_id, source_snapshot_id, generated_at,
        matches, add, add_relations, update, update_relations,
        obsolete, obsolete_relations, supersedes,
        notes, questions (list of {about_new, question, options}).
        """
    ).strip()

    user = "\n\n".join(
        [
            f"project_id={project_id}",
            f"snapshot={snapshot_name}",
            f"model={model}",
            seed_summary,
            format_decisions("existing decisions (canonical)", canonical_decisions),
            format_decisions("new decisions (snapshot)", snapshot_decisions),
            "Instructions:\n"
            "- Keep add/update fields exactly as the seed provides.\n"
            "- Propose supersedes: which new decisions replace which old ones.\n"
            "- If a new decision replaces an old one, add supersedes {new, old:[...]}; optionally mark obsolete[].\n"
            "- If uncertain, add a question and leave supersedes/obsolete empty.\n"
            "- Respond with JSON ONLY.",
        ]
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# -------------------------------
# Main
# -------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Suggest full update_plan (v1.1): use mechanical seed for add/update; model proposes supersedes/obsolete/questions."
    )
    ap.add_argument(
        "--canonical-nodes",
        default="data/hakone-e2/info_nodes_v1.json",
        help="Canonical nodes JSON path",
    )
    ap.add_argument(
        "--canonical-relations",
        default="data/hakone-e2/info_relations_v1.json",
        help="Canonical relations JSON path",
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
        help="Where to write the suggested update_plan JSON",
    )
    ap.add_argument(
        "--seed-plan",
        help="Optional seed plan JSON (if omitted, a mechanical v0.1 seed is generated)",
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
    canonical_rels = load_json(Path(args.canonical_relations), [])
    snapshot = load_json(snapshot_path, {})
    aya = snapshot.get("aya_output", {}) if isinstance(snapshot, dict) else {}
    snap_nodes = aya.get("info_nodes", []) or []
    snap_rels = aya.get("info_relations", []) or []

    # Seed plan: either provided or generated
    if args.seed_plan:
        seed_plan = load_json(Path(args.seed_plan), {})
    else:
        seed_plan = seed_plan_from_snapshot(
            canonical_nodes, canonical_rels, snap_nodes, snap_rels, snapshot_name
        )

    canonical_decisions = summarize_decisions(canonical_nodes)
    snapshot_decisions = summarize_decisions(snap_nodes)

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    # If there are no decision nodes to compare, skip model call and return seed as-is.
    if not canonical_decisions or not snapshot_decisions:
        seed_plan["generated_at"] = generated_at
        seed_plan.setdefault("questions", []).append(
            {
                "question": "No decision nodes to compare; nothing to suggest.",
                "about_new": None,
                "options": [],
            }
        )
        save_json(Path(args.output), seed_plan)
        print("No decisions found; wrote seed plan with notice.")
        return

    messages = build_messages(
        "hakone-e2",
        snapshot_name,
        model,
        seed_plan,
        canonical_decisions,
        snapshot_decisions,
    )
    content = call_openai(api_key, messages, model, base_url)
    content = strip_code_fences(content)
    try:
        ai = json.loads(content)
    except json.JSONDecodeError as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to parse model response as JSON: {exc}")

    # Assemble final plan: start from seed, then overlay AI semantic proposals.
    plan = dict(seed_plan)
    plan["project_id"] = "hakone-e2"
    plan["source_snapshot_id"] = snapshot_name
    plan["generated_at"] = generated_at
    plan["obsolete"] = ai.get("obsolete", []) or []
    plan["obsolete_relations"] = ai.get("obsolete_relations", []) or []
    plan["supersedes"] = ai.get("supersedes", []) or []
    plan["notes"] = ai.get("notes", plan.get("notes", ""))
    plan["questions"] = ai.get("questions", [])

    save_json(Path(args.output), plan)
    print(
        f"Suggested update_plan written to {args.output} "
        f"(add={len(plan.get('add', []))}, update={len(plan.get('update', []))}, "
        f"supersedes={len(plan.get('supersedes', []))}, obsolete={len(plan.get('obsolete', []))})"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
