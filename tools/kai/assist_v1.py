from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def call_openai(
    api_key: str, messages: list[dict[str, str]], model: str = "gpt-4o"
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1200,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected OpenAI response: {body}") from exc
    return content


def parse_model_output(raw: str) -> tuple[Dict[str, Any], str, list[str]]:
    """Expect the model to return JSON with payload/summary_md/notes keys."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model output was not valid JSON: {raw}") from exc

    payload = data.get("payload") or {}
    summary_md = data.get("summary_md") or ""
    notes = data.get("notes") or []
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not isinstance(summary_md, str):
        raise ValueError("summary_md must be a string")
    if not isinstance(notes, list):
        raise ValueError("notes must be a list")
    return payload, summary_md, notes


def build_messages(
    task_type: str, project_id: str, notes: str, pm_snapshot_yaml: str
) -> list[dict[str, str]]:
    system = (
        "You are Kai-assist v1 for vpm-mini. Follow kai_assist_spec_v1 intent. "
        "Return JSON only, no code fences. Fields: payload, summary_md, notes. "
        "Align payload with kind=inspect_pm_snapshot_prompt_v1 (findings, recommendations)."
    )
    user = (
        f"task_type={task_type}\n"
        f"project_id={project_id}\n"
        f"notes={notes or '(none)'}\n"
        "Goal: Inspect pm_snapshot workflow prompt/description to ensure it only handles C/G/δ/Next "
        "and does not imply pm_snapshot directly updates STATE/weekly. "
        "Identify risky snippets and propose clearer wording.\n"
        "Please return JSON with keys:\n"
        "- payload: {kind, project_id, target_workflow, findings:[{location,snippet,issue,suggestion}], "
        "recommendations:[...]} (keep concise)\n"
        "- summary_md: short Markdown summary (2-4 bullet lines)\n"
        "- notes: optional extra notes\n"
        "Source file (.github/workflows/pm_snapshot.yml) follows:\n"
        f"{pm_snapshot_yaml}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def main() -> None:
    parser = argparse.ArgumentParser(description="Kai-assist v1 executor.")
    parser.add_argument(
        "--project-id", required=True, help="Project ID (vpm-mini for v1)."
    )
    parser.add_argument(
        "--task-type",
        required=True,
        help="Kai-assist task type (inspect_pm_snapshot_prompt_v1).",
    )
    parser.add_argument("--notes", default="", help="Optional human notes.")
    parser.add_argument(
        "--output-json",
        required=True,
        help="Output path for kai_task_response_v1 JSON.",
    )
    args = parser.parse_args()

    if args.task_type != "inspect_pm_snapshot_prompt_v1":
        print(f"Unsupported task_type: {args.task_type}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is required", file=sys.stderr)
        sys.exit(1)

    pm_snapshot_path = Path(".github/workflows/pm_snapshot.yml")
    try:
        pm_snapshot_content = read_file(pm_snapshot_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    messages = build_messages(
        task_type=args.task_type,
        project_id=args.project_id,
        notes=args.notes,
        pm_snapshot_yaml=pm_snapshot_content,
    )

    request_id = f"{iso_now()}_{args.task_type}_{args.project_id}"
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw_reply = call_openai(api_key=api_key, messages=messages)
        payload, summary_md, model_notes = parse_model_output(raw_reply)
        status = "ok"
        notes = model_notes
    except (HTTPError, URLError, RuntimeError, ValueError) as exc:
        status = "error"
        payload = {}
        summary_md = f"Failed to generate task response: {exc}"
        notes = [f"error: {exc}"]

    notes = [
        "source: .github/workflows/pm_snapshot.yml",
        f"task: {args.task_type}",
    ] + notes
    if args.notes:
        notes.append(f"human_notes: {args.notes}")

    response: Dict[str, Any] = {
        "version": "kai_task_response_v1",
        "request_id": request_id,
        "status": status,
        "task_type": args.task_type,
        "payload": payload,
        "summary_md": summary_md,
        "notes": notes,
    }

    output_path.write_text(
        json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
