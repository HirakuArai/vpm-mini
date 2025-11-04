#!/usr/bin/env python3
"""
Collect lightweight self-cost indicators for daily reporting.

Outputs a JSON object with:
  external_ip_zero: 1 if there are no unused external IPs, 0 if leftovers, -1 if unknown
  unused_pds_zero:  1 if there are no unused persistent disks, 0 if leftovers, -1 if unknown
  runtime_minutes:  integer minutes for the latest render_manual workflow run, -1 if unavailable
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO = os.environ.get("SELF_COST_REPO", "HirakuArai/vpm-mini")
WORKFLOW_FILE = "render_manual.yml"


def run_command(args: list[str]) -> Optional[str]:
    if not args or shutil.which(args[0]) is None:
        return None
    try:
        result = subprocess.run(
            args,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output if output else ""


def count_lines(args: list[str]) -> Optional[int]:
    output = run_command(args)
    if output is None:
        return None
    lines = [line for line in output.splitlines() if line.strip()]
    return len(lines)


def fetch_latest_render_runtime() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/runs?per_page=1"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "self-cost-collector",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except (HTTPError, URLError, json.JSONDecodeError):
        return -1
    runs = payload.get("workflow_runs") or []
    if not runs:
        return -1
    run = runs[0]
    started_at = run.get("run_started_at") or run.get("created_at")
    completed_at = run.get("updated_at")
    if not started_at or not completed_at:
        return -1
    try:
        start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError:
        return -1
    runtime = end_dt - start_dt
    if runtime.total_seconds() < 0:
        return -1
    return int(runtime.total_seconds() // 60)


def main() -> int:
    addr_count = count_lines(
        [
            "gcloud",
            "-q",
            "compute",
            "addresses",
            "list",
            "--filter=status!=IN_USE",
            "--format=value(address)",
        ]
    )
    pd_count = count_lines(
        [
            "gcloud",
            "-q",
            "compute",
            "disks",
            "list",
            "--filter=-users:*",
            "--format=value(name)",
        ]
    )
    runtime = fetch_latest_render_runtime()

    def as_flag(count: Optional[int]) -> int:
        if count is None:
            return -1
        return 1 if count == 0 else 0

    data = {
        "external_ip_zero": as_flag(addr_count),
        "unused_pds_zero": as_flag(pd_count),
        "runtime_minutes": runtime,
        "counts": {
            "unused_external_ips": addr_count if addr_count is not None else -1,
            "unused_pds": pd_count if pd_count is not None else -1,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
