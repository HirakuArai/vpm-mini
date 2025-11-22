#!/usr/bin/env python3
"""
Mini Loop v0 job runner draft.

Usage:
    python tools/job_runner.py jobs/queue/<job_id>.json

The runner:
- reads the job JSON (v0 format)
- executes the script in the specified workdir
- writes a report to report_path
- exits with the final command's exit code
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from typing import Any, Dict, List


REQUIRED_FIELDS = {"id", "kind", "workdir", "script", "dod", "report_path"}
SUPPORTED_KINDS = {"run_shell"}


def load_job(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")
    if data["kind"] not in SUPPORTED_KINDS:
        raise ValueError(f"Unsupported kind: {data['kind']}")
    if not isinstance(data["script"], list) or not all(
        isinstance(cmd, str) for cmd in data["script"]
    ):
        raise ValueError("script must be a list of strings")
    return data


def ensure_report_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def run_commands(commands: List[str], workdir: str) -> Dict[str, Any]:
    results = []
    final_exit_code = 0
    for cmd in commands:
        print(f"[INFO] Running: {cmd}")
        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        results.append(
            {
                "command": cmd,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            final_exit_code = completed.returncode
            break
        final_exit_code = completed.returncode
    return {"results": results, "exit_code": final_exit_code}


def evaluate_dod(dod_expr: str, exit_code: int) -> bool:
    # v0: only supports "exit_code == 0"
    return dod_expr.strip() == "exit_code == 0" and exit_code == 0


def format_report(
    job: Dict[str, Any], command_results: Dict[str, Any], success: bool
) -> str:
    lines = []
    now = datetime.datetime.utcnow().isoformat() + "Z"
    lines.append(f"job_id: {job['id']}")
    lines.append(f"kind: {job['kind']}")
    lines.append(f"workdir: {job['workdir']}")
    lines.append(f"executed_at: {now}")
    lines.append("")
    lines.append("commands:")
    for idx, res in enumerate(command_results["results"], start=1):
        lines.append(f"  - step: {idx}")
        lines.append(f"    command: {res['command']}")
        lines.append(f"    exit_code: {res['exit_code']}")
        lines.append("    stdout:")
        for line in (res["stdout"] or "").splitlines():
            lines.append(f"      {line}")
        lines.append("    stderr:")
        for line in (res["stderr"] or "").splitlines():
            lines.append(f"      {line}")
    lines.append("")
    lines.append(f"final_exit_code: {command_results['exit_code']}")
    lines.append(f"dod: {job['dod']}")
    lines.append(f"success: {str(success).lower()}")
    lines.append("")
    lines.append("# TODO: move processed job to jobs/done/")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mini Loop v0 job runner (draft)")
    parser.add_argument(
        "job_path", help="Path to job JSON file (e.g., jobs/queue/2025-11-XX-001.json)"
    )
    args = parser.parse_args()

    try:
        job = load_job(args.job_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] Loaded job {job['id']} (kind={job['kind']})")
    try:
        command_results = run_commands(job["script"], job["workdir"])
    except FileNotFoundError as exc:
        print(f"[ERROR] workdir not found: {exc}", file=sys.stderr)
        return 1
    success = evaluate_dod(job["dod"], command_results["exit_code"])
    ensure_report_dir(job["report_path"])
    report_text = format_report(job, command_results, success)
    with open(job["report_path"], "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[INFO] Report written to {job['report_path']}")
    print(f"[INFO] exit_code={command_results['exit_code']}, success={success}")
    return command_results["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
