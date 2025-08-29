#!/usr/bin/env python3
"""
Phase 5-2: Promotion Snapshot Generator
Converts canary promotion results into markdown snapshot report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    print("Error: jinja2 is required. Install with: pip install jinja2")
    sys.exit(1)


def load_promotion_data(input_file: Path) -> dict:
    """Load canary promotion results from JSON file."""
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


def calculate_statistics(promotion_data: dict) -> dict:
    """Calculate summary statistics from promotion data."""
    phases = promotion_data.get("phases", [])

    stats = {
        "total_phases": len(phases),
        "successful_phases": len([p for p in phases if p.get("result") == "PASS"]),
        "failed_phases": len([p for p in phases if p.get("result") == "FAIL"]),
        "total_requests": sum(p.get("total_requests", 0) for p in phases),
        "total_errors": sum(p.get("error_count", 0) for p in phases),
        "avg_success_rate": 0,
        "min_success_rate": 100,
        "max_success_rate": 0,
        "total_duration": 0,
    }

    if phases:
        success_rates = [
            p.get("success_rate", 0)
            for p in phases
            if p.get("success_rate") is not None
        ]
        if success_rates:
            stats["avg_success_rate"] = sum(success_rates) / len(success_rates)
            stats["min_success_rate"] = min(success_rates)
            stats["max_success_rate"] = max(success_rates)

    # Calculate total duration from phase durations
    for phase in phases:
        if "duration" in phase:
            stats["total_duration"] += phase["duration"]

    return stats


def format_phase_table(phases: list) -> str:
    """Generate markdown table for promotion phases."""
    if not phases:
        return "No phases recorded"

    table_lines = [
        "| Phase | Weight | Duration | Requests | Success Rate | RPS | Result |",
        "|-------|--------|----------|----------|--------------|-----|--------|",
    ]

    for phase in phases:
        weight = phase.get("weight", "Unknown")
        duration = f"{phase.get('duration', 0)}s"
        requests = phase.get("total_requests", 0)
        success_rate = f"{phase.get('success_rate', 0):.1f}%"
        rps = f"{phase.get('rps', 0):.1f}"
        result = phase.get("result", "Unknown")

        # Add emoji for result
        result_emoji = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
        result_display = f"{result_emoji} {result}"

        table_lines.append(
            f"| {phase.get('phase', 'Unknown')} | {weight} | {duration} | {requests} | {success_rate} | {rps} | {result_display} |"
        )

    return "\n".join(table_lines)


def format_slo_gates(phases: list) -> str:
    """Generate SLO gate validation summary."""
    slo_results = []

    for phase in phases:
        slo_gates = phase.get("slo_gates", {})
        if slo_gates:
            phase_name = phase.get("phase", "Unknown")

            for gate_name, gate_result in slo_gates.items():
                status = "✅ PASS" if gate_result else "❌ FAIL"
                slo_results.append(f"- **{phase_name} - {gate_name}**: {status}")

    return (
        "\n".join(slo_results) if slo_results else "No SLO gate information available"
    )


def generate_status_emoji(status: str) -> str:
    """Generate appropriate emoji for overall status."""
    status_lower = status.lower()
    if status_lower in ["success", "completed", "pass"]:
        return "🎉"
    elif status_lower in ["failed", "error", "fail"]:
        return "❌"
    elif status_lower in ["partial", "warning"]:
        return "⚠️"
    else:
        return "📊"


def render_snapshot(template_content: str, promotion_data: dict, stats: dict) -> str:
    """Render the markdown snapshot using template and data."""

    # Prepare template variables
    template_vars = {
        # Basic info
        "TIMESTAMP": promotion_data.get(
            "timestamp", datetime.utcnow().isoformat() + "Z"
        ),
        "COMMIT": promotion_data.get("commit", "unknown"),
        "STATUS": promotion_data.get("status", "unknown"),
        "STATUS_EMOJI": generate_status_emoji(promotion_data.get("status", "unknown")),
        # Configuration
        "TARGET_URL": promotion_data.get("config", {}).get("url", "unknown"),
        "PROMOTION_STRATEGY": promotion_data.get("config", {}).get(
            "strategy", "canary"
        ),
        "SLO_THRESHOLD": promotion_data.get("config", {}).get("slo_threshold", "99.0"),
        # Statistics
        "TOTAL_PHASES": stats["total_phases"],
        "SUCCESSFUL_PHASES": stats["successful_phases"],
        "FAILED_PHASES": stats["failed_phases"],
        "TOTAL_REQUESTS": stats["total_requests"],
        "TOTAL_ERRORS": stats["total_errors"],
        "AVG_SUCCESS_RATE": f"{stats['avg_success_rate']:.1f}",
        "MIN_SUCCESS_RATE": f"{stats['min_success_rate']:.1f}",
        "MAX_SUCCESS_RATE": f"{stats['max_success_rate']:.1f}",
        "TOTAL_DURATION": f"{stats['total_duration']}s",
        # Final metrics
        "FINAL_SUCCESS_RATE": promotion_data.get("final_metrics", {}).get(
            "success_rate", 0
        ),
        "FINAL_RPS": promotion_data.get("final_metrics", {}).get("rps", 0),
        "FINAL_LATENCY": promotion_data.get("final_metrics", {}).get("latency_p50", 0),
        # Tables and sections
        "PHASE_TABLE": format_phase_table(promotion_data.get("phases", [])),
        "SLO_GATES": format_slo_gates(promotion_data.get("phases", [])),
        # Success indicators
        "OVERALL_SUCCESS": (
            "✅ SUCCESS" if promotion_data.get("status") == "success" else "❌ FAILED"
        ),
        "SLO_VALIDATION": (
            "✅ PASSED" if stats["min_success_rate"] >= 99.0 else "⚠️ PARTIAL"
        ),
        # Generation metadata
        "GENERATION_TIME": datetime.utcnow().isoformat() + "Z",
        "GENERATOR_VERSION": "1.0",
    }

    # Create Jinja2 template and render
    template = Template(template_content)
    rendered = template.render(**template_vars)

    return rendered


def main():
    parser = argparse.ArgumentParser(
        description="Generate canary promotion snapshot report"
    )
    parser.add_argument(
        "--template", type=Path, required=True, help="Template markdown file path"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input JSON file with promotion data"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output markdown file path"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Loading promotion data from: {args.input}")

    # Load data
    promotion_data = load_promotion_data(args.input)

    if args.verbose:
        print(
            f"Loaded promotion data for commit: {promotion_data.get('commit', 'unknown')}"
        )
        print(f"Status: {promotion_data.get('status', 'unknown')}")
        print(f"Phases: {len(promotion_data.get('phases', []))}")

    # Calculate statistics
    stats = calculate_statistics(promotion_data)

    if args.verbose:
        print(f"Statistics calculated - Total requests: {stats['total_requests']}")
        print(f"Average success rate: {stats['avg_success_rate']:.1f}%")

    # Load template
    template_content = load_template(args.template)

    if args.verbose:
        print(f"Template loaded from: {args.template}")

    # Render snapshot
    rendered_snapshot = render_snapshot(template_content, promotion_data, stats)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(args.output, "w") as f:
        f.write(rendered_snapshot)

    print(f"✅ Snapshot generated successfully: {args.output}")

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
