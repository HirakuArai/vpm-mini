#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_TIMEOUT_SEC = 300
MAX_OPENAI_RETRIES = 3


def read_text(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {label} ({path})")
    return path.read_text(encoding="utf-8")


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


def load_bundle(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing bundle file: {path}")
    data: Dict[str, Any]
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Bundle file must be a JSON/YAML object")
    if "info_source_bundle_v1" in data and isinstance(
        data["info_source_bundle_v1"], dict
    ):
        data = data["info_source_bundle_v1"]
    required = ["project_id", "source_type", "source_id", "raw_text"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise ValueError(f"Bundle missing required fields: {', '.join(missing)}")
    return data


def build_messages(schema_doc: str, bundle: Dict[str, Any]) -> List[Dict[str, str]]:
    project_id = bundle.get("project_id", "")
    source_type = bundle.get("source_type", "")
    source_id = bundle.get("source_id", "")
    title = bundle.get("title", "")
    time_range = bundle.get("time_range", {})
    hints = bundle.get("hints", []) or []
    raw_text = bundle.get("raw_text", "")

    hints_block = "\n".join([f"- {h}" for h in hints]) if hints else "(none)"
    time_range_block = (
        f"from={time_range.get('from','')}, to={time_range.get('to','')}"
        if isinstance(time_range, dict)
        else "(none)"
    )

    system = textwrap.dedent(
        f"""
        You are Kai+Aya for vpm-mini. Convert an info_source_bundle_v1 into info_network JSON.
        Follow docs/pm/info_network_v1_schema.md. Output strictly JSON (no code fences) with keys:
        - kai_plan: summary, estimated_node_count, node_categories (list of {{category,count}}), notes
        - aya_output: info_nodes (array of info_node_v1), info_relations (array of info_relation_v1)
        Keep nodes to ~10-30, relations >= 10 when possible. Do not include extra prose.

        [info_network_v1_schema.md]
        {schema_doc}
        """
    ).strip()

    user = textwrap.dedent(
        f"""
        project_id={project_id}
        source_type={source_type}
        source_id={source_id}
        title={title or '(none)'}
        time_range={time_range_block}

        hints:
        {hints_block}

        raw_text:
        {raw_text}
        """
    ).strip()

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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


def parse_snapshot(raw_text: str) -> Dict[str, Any]:
    cleaned = strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model output is not valid JSON: {cleaned}") from exc

    aya_output = data.get("aya_output")
    if aya_output is None and isinstance(data, dict):
        aya_output = data
    if not isinstance(aya_output, dict):
        raise ValueError("aya_output must be an object")

    info_nodes = aya_output.get("info_nodes")
    info_relations = aya_output.get("info_relations")
    if not isinstance(info_nodes, list) or not isinstance(info_relations, list):
        raise ValueError(
            "aya_output.info_nodes and aya_output.info_relations must exist and be arrays"
        )

    return data


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_dry_run_payload(bundle: Dict[str, Any]) -> Dict[str, Any]:
    project_id = bundle["project_id"]
    source_id = bundle["source_id"]
    return {
        "kai_plan": {
            "summary": f"Dry-run stub for bundle {source_id}.",
            "estimated_node_count": 3,
            "node_categories": [
                {"category": "project_meta", "count": 1},
                {"category": "state_snapshot", "count": 1},
                {"category": "task", "count": 1},
            ],
            "notes": "Stub payload generated because DRY_RUN=1.",
        },
        "aya_output": {
            "info_nodes": [
                {
                    "id": f"{project_id}:fact:bundle-meta:{source_id}",
                    "project_id": project_id,
                    "kind": "fact",
                    "subkind": "project_meta",
                    "title": f"Bundle meta for {source_id}",
                    "summary": "Dry-run bundle meta node.",
                    "body": "This is a stub node generated without calling OpenAI.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": f"bundle:{source_id}",
                        "section_anchor": "meta",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-12-31T00:00:00+09:00",
                    "updated_at": "2025-12-31T00:00:00+09:00",
                    "source_refs": [{"kind": "bundle", "value": source_id}],
                    "authored_by": "kai",
                    "review_status": "unreviewed",
                },
                {
                    "id": f"{project_id}:fact:state_snapshot:{source_id}",
                    "project_id": project_id,
                    "kind": "fact",
                    "subkind": "state_snapshot",
                    "title": f"State snapshot stub ({source_id})",
                    "summary": "Stub state snapshot.",
                    "body": "State snapshot generated in dry-run.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": f"bundle:{source_id}",
                        "section_anchor": "current",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-12-31T00:00:00+09:00",
                    "updated_at": "2025-12-31T00:00:00+09:00",
                    "source_refs": [{"kind": "bundle", "value": source_id}],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
                {
                    "id": f"{project_id}:task:stub:{source_id}",
                    "project_id": project_id,
                    "kind": "task",
                    "subkind": "pm_task",
                    "title": f"Stub task for {source_id}",
                    "summary": "Task stub entry.",
                    "body": "Task description stub.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": f"bundle:{source_id}",
                        "section_anchor": "tasks",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-12-31T00:00:00+09:00",
                    "updated_at": "2025-12-31T00:00:00+09:00",
                    "source_refs": [{"kind": "bundle", "value": source_id}],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
            ],
            "info_relations": [
                {
                    "id": f"{project_id}:rel:stub-1:{source_id}",
                    "project_id": project_id,
                    "type": "part_of",
                    "from": f"{project_id}:fact:state_snapshot:{source_id}",
                    "to": f"{project_id}:fact:bundle-meta:{source_id}",
                    "strength": 0.7,
                    "status": "active",
                    "source_refs": [{"kind": "bundle", "value": source_id}],
                    "created_at": "2025-12-31T00:00:00+09:00",
                    "updated_at": "2025-12-31T00:00:00+09:00",
                },
                {
                    "id": f"{project_id}:rel:stub-2:{source_id}",
                    "project_id": project_id,
                    "type": "derived_from",
                    "from": f"{project_id}:task:stub:{source_id}",
                    "to": f"{project_id}:fact:state_snapshot:{source_id}",
                    "strength": 0.6,
                    "status": "active",
                    "source_refs": [{"kind": "bundle", "value": source_id}],
                    "created_at": "2025-12-31T00:00:00+09:00",
                    "updated_at": "2025-12-31T00:00:00+09:00",
                },
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate info_network snapshot from info_source_bundle_v1."
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="Path to info_source_bundle_v1 (YAML or JSON)",
    )
    parser.add_argument(
        "--schema-doc",
        default="docs/pm/info_network_v1_schema.md",
        help="Path to info_network schema doc (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="Model name (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write generated JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_path = Path(args.bundle)

    try:
        schema_doc = read_text(Path(args.schema_doc), "schema-doc")
        bundle = load_bundle(bundle_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if os.environ.get("DRY_RUN") == "1":
        payload = build_dry_run_payload(bundle)
        write_json(Path(args.output), payload)
        aya_output = payload["aya_output"]
        print(
            f"[DRY_RUN] nodes: {len(aya_output['info_nodes'])}, relations: {len(aya_output['info_relations'])}"
        )
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        return 1
    try:
        base_url = get_openai_base_url()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    messages = build_messages(schema_doc, bundle)

    try:
        raw = call_openai(
            api_key=api_key, messages=messages, model=args.model, base_url=base_url
        )
        snapshot = parse_snapshot(raw)
    except Exception as exc:  # noqa: BLE001
        print(
            f"Failed to generate snapshot (model={args.model}): {exc}", file=sys.stderr
        )
        return 1

    write_json(Path(args.output), snapshot)
    aya_output = snapshot.get("aya_output") or {}
    nodes = aya_output.get("info_nodes") or []
    relations = aya_output.get("info_relations") or []
    print(f"Generated snapshot: nodes={len(nodes)}, relations={len(relations)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
