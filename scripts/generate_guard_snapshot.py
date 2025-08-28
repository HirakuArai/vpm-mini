#!/usr/bin/env python3
"""
Phase 5-3: Guard Snapshot Generator
Converts post-promotion SLO guard results into markdown snapshot report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Template rendering - using simple string replacement instead of jinja2 for simplicity


def load_guard_data(input_file: Path) -> dict:
    """Load SLO guard results from JSON file."""
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        sys.exit(1)


def load_template(template_file: Path) -> str:
    """Load markdown template file."""
    try:
        with open(template_file, "r") as f:
            template_content = f.read()
        return template_content
    except FileNotFoundError:
        print(f"Error: Template file {template_file} not found")
        sys.exit(1)


def generate_threshold_analysis(guard_data: dict) -> str:
    """Generate threshold analysis section."""
    config = guard_data.get("config", {})
    success_rate = guard_data.get("success_rate", 0)
    p50_ms = guard_data.get("p50_ms", 0)
    succ_min = config.get("succ_min", 0.99)
    p50_max = config.get("p50_max", 1000)

    analysis = []

    # Success rate analysis
    if success_rate >= succ_min:
        analysis.append(
            f"✅ **Success Rate**: {success_rate:.1%} ≥ {succ_min:.1%} (PASS)"
        )
    else:
        analysis.append(
            f"❌ **Success Rate**: {success_rate:.1%} < {succ_min:.1%} (FAIL)"
        )

    # Latency analysis
    if p50_ms < p50_max:
        analysis.append(f"✅ **P50 Latency**: {p50_ms}ms < {p50_max}ms (PASS)")
    else:
        analysis.append(f"❌ **P50 Latency**: {p50_ms}ms ≥ {p50_max}ms (FAIL)")

    return "\n".join(analysis)


def generate_status_emoji(guard_ok: bool) -> str:
    """Generate appropriate emoji for guard status."""
    return "✅" if guard_ok else "🚨"


def render_snapshot(template_content: str, guard_data: dict) -> str:
    """Render the markdown snapshot using template and data."""

    # Extract key values with defaults
    config = guard_data.get("config", {})
    statistics = guard_data.get("statistics", {})

    guard_ok = guard_data.get("guard_ok", False)
    rolled_back = guard_data.get("rolled_back", False)
    freeze_on = guard_data.get("freeze_on", False)
    issue_url = guard_data.get("issue_url", "N/A")

    # Prepare template variables
    template_vars = {
        # Basic info
        "TIMESTAMP": guard_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "COMMIT": guard_data.get("commit", "unknown"),
        "STATUS": "SUCCESS" if guard_ok else "GUARD_FAILURE",
        "STATUS_EMOJI": generate_status_emoji(guard_ok),
        # Configuration
        "WINDOW_MIN": config.get("window_min", 10),
        "SUCC_THRESHOLD": f"{config.get('succ_min', 0.99) * 100:.1f}",
        "P50_THRESHOLD": config.get("p50_max", 1000),
        "URL": config.get("url", "unknown"),
        # Results
        "SUCCESS_RATE": f"{guard_data.get('success_rate', 0) * 100:.1f}",
        "P50_MS": guard_data.get("p50_ms", 0),
        "GUARD_STATUS": "✅ PASS" if guard_ok else "❌ FAIL",
        "GUARD_RESULT": "PASS" if guard_ok else "FAIL",
        # Actions
        "ROLLED_BACK": "✅ YES" if rolled_back else "❌ NO",
        "FREEZE_ON": "🚫 YES" if freeze_on else "✅ NO",
        "INCIDENT_CREATED": "✅ YES" if issue_url != "N/A" else "❌ NO",
        "ISSUE_URL": issue_url,
        # Statistics
        "TOTAL_BATCHES": statistics.get("total_batches", 0),
        "MIN_SUCCESS_RATE": f"{statistics.get('min_success_rate', 0) * 100:.1f}",
        "MAX_SUCCESS_RATE": f"{statistics.get('max_success_rate', 0) * 100:.1f}",
        "MIN_P50_MS": statistics.get("min_p50_ms", 0),
        "MAX_P50_MS": statistics.get("max_p50_ms", 0),
        # Analysis
        "THRESHOLD_ANALYSIS": generate_threshold_analysis(guard_data),
        # Status indicators
        "ACTIONS_TAKEN": (
            "Rollback + Freeze"
            if rolled_back and freeze_on
            else "Rollback" if rolled_back else "Freeze" if freeze_on else "None"
        ),
        "ROLLBACK_STATUS": "✅ EXECUTED" if rolled_back else "❌ NOT REQUIRED",
        "FREEZE_STATUS": "🚫 ACTIVE" if freeze_on else "✅ INACTIVE",
        "INCIDENT_STATUS": issue_url if issue_url != "N/A" else "❌ NONE",
        # Conditional flags for template
        "GUARD_PASSED": guard_ok,
        "GUARD_FAILED": not guard_ok,
        # Rollback details
        "ROLLBACK_STAGE": guard_data.get("rollback_stage", "N/A"),
        "ROLLBACK_TIMESTAMP": guard_data.get("rollback_timestamp", "N/A"),
        "ROLLBACK_VERIFICATION": "✅ VERIFIED" if rolled_back else "N/A",
        # Freeze details
        "FREEZE_REASON": guard_data.get(
            "rollback_reason", "post-promotion-slo-guard-failure"
        ),
        "FREEZE_TIMESTAMP": guard_data.get("rollback_timestamp", "N/A"),
        # Generation metadata
        "GENERATION_TIME": datetime.utcnow().isoformat() + "Z",
        "WORKFLOW_URL": "Available in GitHub Actions",
    }

    # Handle simple template format (non-Jinja2 style)
    rendered = template_content
    for key, value in template_vars.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))

    return rendered


def main():
    parser = argparse.ArgumentParser(
        description="Generate post-promotion SLO guard snapshot report"
    )
    parser.add_argument(
        "--template", type=Path, required=True, help="Template markdown file path"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input JSON file with guard data"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output markdown file path"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Loading guard data from: {args.input}")

    # Load data
    guard_data = load_guard_data(args.input)

    if args.verbose:
        print(f"Guard status: {guard_data.get('guard_ok', False)}")
        print(f"Success rate: {guard_data.get('success_rate', 0):.1%}")
        print(f"P50 latency: {guard_data.get('p50_ms', 0)}ms")

    # Load template
    template_content = load_template(args.template)

    if args.verbose:
        print(f"Template loaded from: {args.template}")

    # Render snapshot
    rendered_snapshot = render_snapshot(template_content, guard_data)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(args.output, "w") as f:
        f.write(rendered_snapshot)

    print(f"✅ Guard snapshot generated successfully: {args.output}")

    if args.verbose:
        print(f"Output file size: {args.output.stat().st_size} bytes")
        print("Snapshot preview (first 10 lines):")
        with open(args.output, "r") as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"  {line.rstrip()}")


if __name__ == "__main__":
    main()
