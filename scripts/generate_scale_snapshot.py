#!/usr/bin/env python3
"""
Generate scale verification snapshot report from template and verification results.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_verification_results(results_file):
    """Load verification results from JSON file."""
    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading verification results: {e}")
        sys.exit(1)


def format_status_indicator(met, success_text="✅ PASS", fail_text="❌ FAIL"):
    """Format status indicator based on condition."""
    return success_text if met else fail_text


def format_percentage(value):
    """Format percentage with proper precision."""
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}" if value <= 1.0 else f"{value:.1f}"
    return str(value)


def extract_client_data(results):
    """Extract client data from verification results."""
    client_data = results.get("detailed_results", {}).get("client_data", {})
    latency_stats = client_data.get("latency_stats", {})
    test_config = client_data.get("test_config", {})

    return {
        "rps_effective": client_data.get("rps_effective", 0),
        "total_requests": client_data.get("total_requests", 0),
        "successful_requests": client_data.get("successful_requests", 0),
        "success_rate": client_data.get("success_rate", 0),
        "duration_s": client_data.get("duration_s", 0),
        "p50_ms": latency_stats.get("p50_ms", 0),
        "p95_ms": latency_stats.get("p95_ms", 0),
        "p99_ms": latency_stats.get("p99_ms", 0),
        "min_ms": latency_stats.get("min_ms", 0),
        "max_ms": latency_stats.get("max_ms", 0),
        "status_codes": client_data.get("status_codes", {}),
        "concurrency": test_config.get("concurrency", 200),
        "timeout": test_config.get("timeout_s", 2.0),
        "ramp_up_enabled": "Yes" if test_config.get("ramp_up_enabled", True) else "No",
    }


def generate_snapshot(template_path, output_path, results_file):
    """Generate snapshot report from template and results."""

    # Load data
    results = load_verification_results(results_file)
    template_content = Path(template_path).read_text()

    # Extract core metrics
    test_summary = results.get("test_summary", {})
    performance_metrics = results.get("performance_metrics", {})
    slo_metrics = results.get("slo_metrics", {})
    scaling_metrics = results.get("scaling_metrics", {})
    slo_compliance = results.get("slo_compliance", {})

    # Extract client data
    client_data = extract_client_data(results)

    # Calculate derived metrics
    error_rate = (
        round((1 - client_data["success_rate"]) * 100, 1)
        if client_data["success_rate"] <= 1.0
        else 0
    )
    duration_minutes = round(performance_metrics.get("test_duration_minutes", 0), 1)
    window_minutes = performance_metrics.get("sustained_window_minutes", 5)
    rps_efficiency = round(performance_metrics.get("rps_efficiency", 0) * 100, 1)

    # Istio metrics
    istio_metrics = results.get("detailed_results", {}).get("istio_metrics", {})
    istio_rps = istio_metrics.get("total_rps", 0)

    # Status codes formatting
    status_codes_str = ", ".join(
        [f"{code}: {count}" for code, count in client_data["status_codes"].items()]
    )

    # SLO compliance analysis
    slo_compliance_count = sum(
        1 for slo in slo_compliance.values() if slo.get("met", False)
    )
    total_slo_count = len(slo_compliance)
    slo_compliance_rate = round(
        (slo_compliance_count / max(1, total_slo_count)) * 100, 1
    )

    # Template variables
    template_vars = {
        "DATE": datetime.fromisoformat(
            results.get("timestamp", datetime.now(timezone.utc).isoformat()).replace(
                "Z", "+00:00"
            )
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "COMMIT": results.get("commit", "unknown"),
        "VERIFY_JSON": "reports/phase4_scale_verify.json",
        "OVERALL_STATUS": (
            "SUCCESS" if test_summary.get("overall_success", False) else "FAILED"
        ),
        # Performance metrics
        "CLIENT_RPS": f"{client_data['rps_effective']:.1f}",
        "ISTIO_RPS": f"{istio_rps:.1f}",
        "RPS_EFFICIENCY": f"{rps_efficiency}",
        "DURATION_MINUTES": f"{duration_minutes}",
        "WINDOW_MINUTES": window_minutes,
        # SLO metrics
        "P50_MS": f"{slo_metrics.get('p50_ms', 0):.0f}",
        "P95_MS": f"{slo_metrics.get('p95_ms', 0):.0f}",
        "P99_MS": f"{client_data.get('p99_ms', 0):.0f}",
        "MIN_LATENCY_MS": f"{client_data.get('min_ms', 0)}",
        "MAX_LATENCY_MS": f"{client_data.get('max_ms', 0)}",
        "SUCCESS_RATE": format_percentage(slo_metrics.get("success_rate", 0)),
        "ERROR_RATE": f"{error_rate}",
        # Status indicators
        "P50_STATUS": format_status_indicator(
            slo_compliance.get("p50_latency", {}).get("met", False)
        ),
        "P95_STATUS": format_status_indicator(
            slo_compliance.get("p95_latency", {}).get("met", False)
        ),
        "SUCCESS_RATE_STATUS": format_status_indicator(
            slo_compliance.get("success_rate", {}).get("met", False)
        ),
        "RPS_REQUIREMENT_STATUS": format_status_indicator(
            test_summary.get("meets_rps_requirement", False)
        ),
        "DURATION_REQUIREMENT_STATUS": format_status_indicator(
            test_summary.get("meets_duration_requirement", False)
        ),
        "SUSTAINED_PERFORMANCE_STATUS": format_status_indicator(
            test_summary.get("meets_rps_requirement", False)
            and test_summary.get("meets_duration_requirement", False)
        ),
        # Scaling metrics
        "CURRENT_PODS": scaling_metrics.get("current_pods", 0),
        "SCALING_STATUS": (
            "Yes" if scaling_metrics.get("scaling_detected", False) else "No"
        ),
        "SCALING_REQUIREMENT_STATUS": format_status_indicator(
            scaling_metrics.get("scaling_detected", False), "✅ YES", "⚠️  NO"
        ),
        # Request metrics
        "TOTAL_REQUESTS": f"{client_data['total_requests']:,}",
        "SUCCESSFUL_REQUESTS": f"{client_data['successful_requests']:,}",
        "STATUS_CODES": status_codes_str,
        # Test configuration
        "CONCURRENCY": client_data["concurrency"],
        "TIMEOUT": client_data["timeout"],
        "RAMP_UP_ENABLED": client_data["ramp_up_enabled"],
        # Summary metrics
        "SLO_COMPLIANCE_RATE": f"{slo_compliance_rate}",
    }

    # Replace template variables
    for key, value in template_vars.items():
        placeholder = f"{{{{{key}}}}}"
        template_content = template_content.replace(placeholder, str(value))

    # Write output
    Path(output_path).write_text(template_content)
    print(f"Generated scale verification snapshot: {output_path}")

    # Print summary
    print("\n📊 Scale Verification Summary:")
    print(f"   • Overall Status: {template_vars['OVERALL_STATUS']}")
    print(f"   • Client RPS: {template_vars['CLIENT_RPS']}")
    print(f"   • Duration: {template_vars['DURATION_MINUTES']} minutes")
    print(f"   • Success Rate: {template_vars['SUCCESS_RATE']}%")
    print(f"   • P50 Latency: {template_vars['P50_MS']}ms")
    print(f"   • Pod Scaling: {template_vars['CURRENT_PODS']} pods")


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python3 generate_scale_snapshot.py <template_path> <output_path> <results_file>"
        )
        sys.exit(1)

    template_path = sys.argv[1]
    output_path = sys.argv[2]
    results_file = sys.argv[3]

    generate_snapshot(template_path, output_path, results_file)


if __name__ == "__main__":
    main()
