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


def build_messages(schema: str, job: str, current_state: str) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        f"""
        You are Kai+Aya for vpm-mini. Generate info_network snapshot JSON only (no code fences, no prose).
        Follow docs/pm/info_network_v1_schema.md and docs/projects/hakone-e2/info_network_job_v1.md.

        Return strictly JSON with keys:
        - kai_plan: summary, estimated_node_count, node_categories (list of {{category,count}}), notes
        - aya_output: info_nodes (array of info_node_v1), info_relations (array of info_relation_v1)

        Reference materials:
        [info_network_v1_schema.md]
        {schema}

        [hakone-e2/info_network_job_v1.md]
        {job}
        """
    ).strip()

    user = textwrap.dedent(
        f"""
        project_id=hakone-e2
        Source: STATE/hakone-e2/current_state.md

        Please produce JSON that follows Kai/Aya job v1. Make sure aya_output.info_nodes and aya_output.info_relations exist.
        Output JSON only, no code fences, no Markdown.

        --- STATE/hakone-e2/current_state.md ---
        {current_state}
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


def build_dry_run_payload() -> Dict[str, Any]:
    return {
        "kai_plan": {
            "summary": "Dry-run stub: split hakone-e2 current_state into project meta, C/G/δ, tasks, evidence.",
            "estimated_node_count": 6,
            "node_categories": [
                {"category": "project_meta", "count": 1},
                {"category": "current", "count": 1},
                {"category": "goals", "count": 1},
                {"category": "gap", "count": 1},
                {"category": "tasks", "count": 1},
                {"category": "evidence", "count": 1},
            ],
            "notes": "Stub payload generated because DRY_RUN=1.",
        },
        "aya_output": {
            "info_nodes": [
                {
                    "id": "hakone-e2:fact:project_meta:dryrun-1",
                    "project_id": "hakone-e2",
                    "kind": "fact",
                    "subkind": "project_meta",
                    "title": "Hakone-e2 overview (dry-run)",
                    "summary": "Project overview stub for dry-run.",
                    "body": "This is a stub node generated without calling OpenAI.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "overview",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "kai",
                    "review_status": "unreviewed",
                },
                {
                    "id": "hakone-e2:fact:state_snapshot:dryrun-1",
                    "project_id": "hakone-e2",
                    "kind": "fact",
                    "subkind": "state_snapshot",
                    "title": "Current state (dry-run)",
                    "summary": "Current state stub.",
                    "body": "State snapshot stub entry.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "current",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
                {
                    "id": "hakone-e2:fact:goal:dryrun-1",
                    "project_id": "hakone-e2",
                    "kind": "fact",
                    "subkind": "state_snapshot",
                    "title": "Goal stub (dry-run)",
                    "summary": "Goal stub entry.",
                    "body": "Goal description stub.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "goals",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
                {
                    "id": "hakone-e2:fact:gap:dryrun-1",
                    "project_id": "hakone-e2",
                    "kind": "fact",
                    "subkind": "state_snapshot",
                    "title": "Gap stub (dry-run)",
                    "summary": "Gap stub entry.",
                    "body": "Gap description stub.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "gap",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
                {
                    "id": "hakone-e2:task:H2-DRYRUN-1",
                    "project_id": "hakone-e2",
                    "kind": "task",
                    "subkind": "pm_task",
                    "title": "Dry-run task placeholder",
                    "summary": "Task stub entry.",
                    "body": "Task description stub.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "tasks",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
                {
                    "id": "hakone-e2:fact:evidence:dryrun-1",
                    "project_id": "hakone-e2",
                    "kind": "fact",
                    "subkind": "weekly_summary",
                    "title": "Evidence stub (dry-run)",
                    "summary": "Evidence stub entry.",
                    "body": "Evidence description stub.",
                    "scope": {
                        "project_phase": "phase1",
                        "lane": "pm_core",
                        "file": "STATE/hakone-e2/current_state.md",
                        "section_anchor": "evidence",
                    },
                    "status": "active",
                    "importance": "normal",
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "authored_by": "aya",
                    "review_status": "unreviewed",
                },
            ],
            "info_relations": [
                {
                    "id": "hakone-e2:rel:dryrun-1",
                    "project_id": "hakone-e2",
                    "type": "part_of",
                    "from": "hakone-e2:fact:state_snapshot:dryrun-1",
                    "to": "hakone-e2:fact:project_meta:dryrun-1",
                    "strength": 0.8,
                    "status": "active",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                },
                {
                    "id": "hakone-e2:rel:dryrun-2",
                    "project_id": "hakone-e2",
                    "type": "evidence_for",
                    "from": "hakone-e2:fact:evidence:dryrun-1",
                    "to": "hakone-e2:fact:state_snapshot:dryrun-1",
                    "strength": 0.7,
                    "status": "active",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                },
                {
                    "id": "hakone-e2:rel:dryrun-3",
                    "project_id": "hakone-e2",
                    "type": "derived_from",
                    "from": "hakone-e2:task:H2-DRYRUN-1",
                    "to": "hakone-e2:fact:gap:dryrun-1",
                    "strength": 0.6,
                    "status": "active",
                    "source_refs": [
                        {"kind": "file", "value": "STATE/hakone-e2/current_state.md"}
                    ],
                    "created_at": "2025-11-30T00:00:00+09:00",
                    "updated_at": "2025-11-30T00:00:00+09:00",
                },
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate hakone-e2 info_network snapshot via OpenAI (Kai+Aya)."
    )
    parser.add_argument(
        "--current-state",
        default="STATE/hakone-e2/current_state.md",
        help="Path to current_state markdown (default: %(default)s)",
    )
    parser.add_argument(
        "--schema-doc",
        default="docs/pm/info_network_v1_schema.md",
        help="Path to info_network schema doc (default: %(default)s)",
    )
    parser.add_argument(
        "--job-doc",
        default="docs/projects/hakone-e2/info_network_job_v1.md",
        help="Path to job spec doc (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="Model name (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="reports/hakone-e2/info_snapshot_v1_raw.json",
        help="Path to write generated JSON (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        current_state = read_text(Path(args.current_state), "current_state")
        schema_doc = read_text(Path(args.schema_doc), "schema-doc")
        job_doc = read_text(Path(args.job_doc), "job-doc")
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if os.environ.get("DRY_RUN") == "1":
        payload = build_dry_run_payload()
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

    messages = build_messages(schema_doc, job_doc, current_state)

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
