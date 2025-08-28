#!/usr/bin/env python3
"""
Generate promotion snapshot report from template and promotion results.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_promotion_results(results_file):
    """Load promotion results from JSON file."""
    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading promotion results: {e}")
        sys.exit(1)


def extract_stage_data(results, stage_name):
    """Extract data for a specific stage."""
    stages = results.get("stages", {})
    stage_data = stages.get(stage_name, {})

    return {
        "gate_ok": "✅ PASS" if stage_data.get("gate_ok", False) else "❌ FAIL",
        "final_ok": "✅ PASS" if stage_data.get("final_ok", False) else "❌ FAIL",
        "p50": stage_data.get("p50_ms", 0),
        "success_rate": round(stage_data.get("success_rate", 0) * 100, 1),
        "v2_share": round(stage_data.get("v2_share", 0) * 100, 1),
    }


def generate_snapshot(template_path, output_path, results_file):
    """Generate snapshot report from template and results."""

    # Load data
    results = load_promotion_results(results_file)
    template_content = Path(template_path).read_text()

    # Extract metadata
    timestamp = results.get("timestamp", datetime.now(timezone.utc).isoformat())
    commit = results.get("commit", "unknown")
    promotion_status = "SUCCESS" if results.get("all_gates_passed", False) else "FAILED"

    # Extract stage data
    stage_90_10 = extract_stage_data(results, "90:10")
    stage_50_50 = extract_stage_data(results, "50:50")
    stage_100_0 = extract_stage_data(results, "100:0")

    # Template variables
    template_vars = {
        "DATE": datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "COMMIT": commit,
        "VERIFY_JSON": "reports/phase4_canary_promotion.json",
        "PROMOTION_STATUS": promotion_status,
        "FINAL_V2_SHARE": stage_100_0["v2_share"],
        # Stage 90:10
        "STAGE_90_10_GATE_OK": stage_90_10["gate_ok"],
        "STAGE_90_10_P50": stage_90_10["p50"],
        "STAGE_90_10_SUCCESS_RATE": stage_90_10["success_rate"],
        "STAGE_90_10_V2_SHARE": stage_90_10["v2_share"],
        # Stage 50:50
        "STAGE_50_50_GATE_OK": stage_50_50["gate_ok"],
        "STAGE_50_50_P50": stage_50_50["p50"],
        "STAGE_50_50_SUCCESS_RATE": stage_50_50["success_rate"],
        "STAGE_50_50_V2_SHARE": stage_50_50["v2_share"],
        # Stage 100:0
        "STAGE_100_0_GATE_OK": stage_100_0["gate_ok"],
        "STAGE_100_0_FINAL_OK": stage_100_0["final_ok"],
        "STAGE_100_0_P50": stage_100_0["p50"],
        "STAGE_100_0_SUCCESS_RATE": stage_100_0["success_rate"],
        "STAGE_100_0_V2_SHARE": stage_100_0["v2_share"],
    }

    # Replace template variables
    for key, value in template_vars.items():
        placeholder = f"{{{{{key}}}}}"
        template_content = template_content.replace(placeholder, str(value))

    # Write output
    Path(output_path).write_text(template_content)
    print(f"Generated promotion snapshot: {output_path}")


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python3 generate_promotion_snapshot.py <template_path> <output_path> <results_file>"
        )
        sys.exit(1)

    template_path = sys.argv[1]
    output_path = sys.argv[2]
    results_file = sys.argv[3]

    generate_snapshot(template_path, output_path, results_file)


if __name__ == "__main__":
    main()
