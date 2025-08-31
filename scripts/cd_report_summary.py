#!/usr/bin/env python3
"""
CD Report Summary Generator
Reads reports/cd_runs.ndjson and generates reports/cd_summary.json
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


def load_ndjson_runs(filepath: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Load last N runs from NDJSON file"""
    runs = []
    if not os.path.exists(filepath):
        return runs

    with open(filepath, "r") as f:
        lines = f.readlines()
        # Get last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        for line in recent_lines:
            try:
                runs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return runs


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile from a list of values"""
    if not values:
        return 0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * percentile / 100
    f = int(k)
    c = f + 1 if f < len(sorted_vals) - 1 else f
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def generate_summary(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from runs"""
    if not runs:
        return {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "total_runs": 0,
            "success_rate": 0.0,
            "freeze_rate": 0.0,
            "fail_rate": 0.0,
            "p50_duration_sec": {"A": 0, "B": 0},
            "p95_duration_sec": {"A": 0, "B": 0},
            "last_run": None,
        }

    # Count statuses
    total = len(runs)
    success_count = sum(1 for r in runs if r.get("status") == "success")
    freeze_count = sum(1 for r in runs if r.get("status") == "freeze")
    fail_count = sum(1 for r in runs if r.get("status") == "failed")

    # Collect durations for successful runs
    a_durations = []
    b_durations = []
    for run in runs:
        if run.get("status") == "success" and "clusters" in run:
            if "A" in run["clusters"] and "duration_sec" in run["clusters"]["A"]:
                a_durations.append(run["clusters"]["A"]["duration_sec"])
            if "B" in run["clusters"] and "duration_sec" in run["clusters"]["B"]:
                b_durations.append(run["clusters"]["B"]["duration_sec"])

    return {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "total_runs": total,
        "success_rate": round(success_count / total, 3) if total > 0 else 0.0,
        "freeze_rate": round(freeze_count / total, 3) if total > 0 else 0.0,
        "fail_rate": round(fail_count / total, 3) if total > 0 else 0.0,
        "p50_duration_sec": {
            "A": int(calculate_percentile(a_durations, 50)) if a_durations else 0,
            "B": int(calculate_percentile(b_durations, 50)) if b_durations else 0,
        },
        "p95_duration_sec": {
            "A": int(calculate_percentile(a_durations, 95)) if a_durations else 0,
            "B": int(calculate_percentile(b_durations, 95)) if b_durations else 0,
        },
        "last_run": runs[-1] if runs else None,
    }


def main():
    """Main entry point"""
    ndjson_path = "reports/cd_runs.ndjson"
    summary_path = "reports/cd_summary.json"

    # Load recent runs
    runs = load_ndjson_runs(ndjson_path, limit=100)

    # Generate summary
    summary = generate_summary(runs)

    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)

    # Write summary
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary generated: {len(runs)} runs analyzed")
    print(f"Success rate: {summary['success_rate']:.1%}")
    print(
        f"P95 duration: A={summary['p95_duration_sec']['A']}s, B={summary['p95_duration_sec']['B']}s"
    )


if __name__ == "__main__":
    main()
