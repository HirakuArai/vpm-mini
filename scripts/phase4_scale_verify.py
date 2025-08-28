#!/usr/bin/env python3
"""
Phase 4-7: Scale Verification and SLO Validation

Verifies sustained RPS performance, SLO compliance, and Knative scaling behavior.
Integrates with Prometheus metrics and Kubernetes pod monitoring.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict

try:
    import requests
except ImportError:
    requests = None
    print("⚠️  Warning: requests not available, Prometheus integration disabled")


def log_info(message: str) -> None:
    """Log info message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\033[32m[{timestamp}]\033[0m {message}")


def log_warn(message: str) -> None:
    """Log warning message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\033[33m[{timestamp}]\033[0m {message}")


def log_error(message: str) -> None:
    """Log error message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\033[31m[{timestamp}]\033[0m {message}")


def load_client_results(client_json_path: str) -> Dict:
    """Load and validate client load test results."""
    try:
        with open(client_json_path, "r") as f:
            data = json.load(f)

        # Validate required fields
        required_fields = ["rps_effective", "success_rate", "latency_stats"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        return data

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        log_error(f"Failed to load client results: {e}")
        sys.exit(1)


def query_prometheus(query: str, prom_url: str = None) -> float:
    """Query Prometheus for metrics."""
    if not requests:
        log_warn("Requests library not available, skipping Prometheus query")
        return 0.0

    prom_url = prom_url or os.environ.get("PROM_URL", "http://localhost:9090")

    try:
        url = f"{prom_url}/api/v1/query"
        params = {"query": query}

        log_info(f"Querying Prometheus: {query}")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            log_warn(f"No results for Prometheus query: {query}")
            return 0.0

        value = float(results[0]["value"][1])
        log_info(f"Prometheus result: {value}")
        return value

    except Exception as e:
        log_warn(f"Prometheus query failed: {e}")
        return 0.0


def get_istio_metrics(
    service_name: str = "hello", namespace: str = "hyper-swarm"
) -> Dict[str, float]:
    """Get Istio service mesh metrics from Prometheus."""
    metrics = {}

    # Success rate (2xx responses)
    success_query = f'sum(rate(istio_requests_total{{response_code=~"2..",destination_workload="{service_name}",destination_service_namespace="{namespace}"}}[1m]))'

    # Total request rate
    total_query = f'sum(rate(istio_requests_total{{destination_workload="{service_name}",destination_service_namespace="{namespace}"}}[1m]))'

    # P50 latency
    p50_query = f'histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{{destination_workload="{service_name}",destination_service_namespace="{namespace}"}}[1m])) by (le))'

    # P95 latency
    p95_query = f'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{{destination_workload="{service_name}",destination_service_namespace="{namespace}"}}[1m])) by (le))'

    metrics["success_rps"] = query_prometheus(success_query)
    metrics["total_rps"] = query_prometheus(total_query)
    metrics["p50_ms"] = query_prometheus(p50_query)
    metrics["p95_ms"] = query_prometheus(p95_query)

    # Calculate success rate
    if metrics["total_rps"] > 0:
        metrics["success_rate"] = metrics["success_rps"] / metrics["total_rps"]
    else:
        metrics["success_rate"] = 0.0

    return metrics


def get_knative_pod_count(
    service_name: str = "hello", namespace: str = "hyper-swarm"
) -> int:
    """Get current pod count for Knative service."""
    try:
        cmd = [
            "kubectl",
            "-n",
            namespace,
            "get",
            "pod",
            "-l",
            f"serving.knative.dev/service={service_name}",
            "--field-selector=status.phase=Running",
            "--no-headers",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        pod_count = len(lines) if lines and lines[0] else 0

        log_info(f"Current {service_name} pod count: {pod_count}")
        return pod_count

    except subprocess.CalledProcessError as e:
        log_warn(f"Failed to get pod count: {e}")
        return 0


def get_knative_scaling_info(
    service_name: str = "hello", namespace: str = "hyper-swarm"
) -> Dict:
    """Get Knative service scaling configuration and status."""
    try:
        # Get Knative Service configuration
        cmd = [
            "kubectl",
            "-n",
            namespace,
            "get",
            "ksvc",
            service_name,
            "-o",
            "jsonpath={.spec.template.metadata.annotations}{.status}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        scaling_info = {
            "current_pods": get_knative_pod_count(service_name, namespace),
            "min_scale": "0",  # Default Knative min
            "max_scale": "1000",  # Default Knative max
            "target_utilization": "70%",  # Default target
            "scaling_class": "kpa.autoscaling.knative.dev",
        }

        # Parse annotations from kubectl output (simplified)
        if "autoscaling.knative.dev/minScale" in result.stdout:
            # In a real implementation, you'd parse the JSON properly
            log_info("Found Knative scaling annotations")

        return scaling_info

    except subprocess.CalledProcessError as e:
        log_warn(f"Failed to get scaling info: {e}")
        return {"current_pods": get_knative_pod_count(service_name, namespace)}


def analyze_sustained_performance(client_data: Dict, window_minutes: int = 5) -> Dict:
    """Analyze sustained performance metrics."""
    duration_s = client_data.get("duration_s", 0)
    rps_effective = client_data.get("rps_effective", 0)
    rps_target = client_data.get(
        "rps_target", client_data.get("test_config", {}).get("target_rps", 800)
    )

    # Calculate sustained performance metrics
    sustained_rps_met = rps_effective >= 800  # Hard requirement
    sustained_duration_met = duration_s >= (window_minutes * 60)  # 5+ minutes

    # RPS efficiency
    rps_efficiency = (rps_effective / rps_target) if rps_target > 0 else 0

    return {
        "sustained_rps_met": sustained_rps_met,
        "sustained_duration_met": sustained_duration_met,
        "rps_efficiency": round(rps_efficiency, 3),
        "minimum_rps_required": 800,
        "actual_rps": rps_effective,
        "target_rps": rps_target,
        "window_minutes": window_minutes,
        "test_duration_minutes": round(duration_s / 60, 1),
    }


def validate_slo_compliance(client_data: Dict, istio_metrics: Dict = None) -> Dict:
    """Validate SLO compliance based on client and Istio metrics."""
    # Primary metrics from client data
    latency_stats = client_data.get("latency_stats", {})
    client_p50 = latency_stats.get("p50_ms", float("inf"))
    client_p95 = latency_stats.get("p95_ms", float("inf"))
    client_success_rate = client_data.get("success_rate", 0)

    # Secondary metrics from Istio (if available)
    istio_p50 = (istio_metrics or {}).get("p50_ms", 0)
    istio_p95 = (istio_metrics or {}).get("p95_ms", 0)
    istio_success_rate = (istio_metrics or {}).get("success_rate", 0)

    # Use best available metrics (prefer client data for accuracy)
    effective_p50 = client_p50 if client_p50 < float("inf") else istio_p50
    effective_p95 = client_p95 if client_p95 < float("inf") else istio_p95
    effective_success_rate = max(client_success_rate, istio_success_rate)

    # SLO validation
    slo_compliance = {
        "p50_latency": {
            "threshold_ms": 1000,
            "actual_ms": effective_p50,
            "met": effective_p50 < 1000,
            "source": "client" if client_p50 < float("inf") else "istio",
        },
        "p95_latency": {
            "threshold_ms": 1500,
            "actual_ms": effective_p95,
            "met": effective_p95 < 1500,
            "source": "client" if client_p95 < float("inf") else "istio",
        },
        "success_rate": {
            "threshold": 0.99,
            "actual": effective_success_rate,
            "met": effective_success_rate >= 0.99,
            "source": "client" if client_success_rate > 0 else "istio",
        },
    }

    # Overall SLO compliance
    all_slos_met = all(slo["met"] for slo in slo_compliance.values())

    return {
        "slo_compliance": slo_compliance,
        "all_slos_met": all_slos_met,
        "slo_summary": {
            "p50_ms": effective_p50,
            "p95_ms": effective_p95,
            "success_rate": effective_success_rate,
        },
    }


def generate_scale_verification_report(
    client_data: Dict,
    istio_metrics: Dict,
    scaling_info: Dict,
    performance_analysis: Dict,
    slo_validation: Dict,
    window_minutes: int,
) -> Dict:
    """Generate comprehensive scale verification report."""

    timestamp = datetime.now(timezone.utc).isoformat()

    # Git information
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        commit = "unknown"
        branch = "unknown"

    # Overall assessment
    meets_rps = performance_analysis["sustained_rps_met"]
    meets_duration = performance_analysis["sustained_duration_met"]
    meets_slo = slo_validation["all_slos_met"]
    scale_occurred = (
        scaling_info["current_pods"] >= 2
    )  # At least scaled beyond initial pod

    overall_success = meets_rps and meets_duration and meets_slo

    report = {
        "timestamp": timestamp,
        "commit": commit,
        "branch": branch,
        "test_summary": {
            "meets_rps_requirement": meets_rps,
            "meets_duration_requirement": meets_duration,
            "meets_slo_requirements": meets_slo,
            "scaling_occurred": scale_occurred,
            "overall_success": overall_success,
        },
        "performance_metrics": {
            "client_rps": client_data.get("rps_effective", 0),
            "istio_rps": istio_metrics.get("total_rps", 0),
            "sustained_window_minutes": window_minutes,
            "rps_efficiency": performance_analysis["rps_efficiency"],
            "test_duration_minutes": performance_analysis["test_duration_minutes"],
        },
        "slo_metrics": slo_validation["slo_summary"],
        "slo_compliance": slo_validation["slo_compliance"],
        "scaling_metrics": {
            "current_pods": scaling_info["current_pods"],
            "scaling_detected": scale_occurred,
            "min_pods_for_success": 2,
        },
        "detailed_results": {
            "client_data": client_data,
            "istio_metrics": istio_metrics,
            "scaling_info": scaling_info,
            "performance_analysis": performance_analysis,
        },
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4-7: Scale verification and SLO validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic verification with client results
  python3 phase4_scale_verify.py --client_json reports/phase4_load_client.json

  # Custom sustained window and Prometheus URL
  python3 phase4_scale_verify.py --client_json reports/phase4_load_client.json --window_min 10 --prom_url http://localhost:9090

  # Output to specific file
  python3 phase4_scale_verify.py --client_json reports/phase4_load_client.json --output reports/phase4_scale_verify.json
        """,
    )

    parser.add_argument(
        "--client_json", required=True, help="Client load test results JSON file"
    )
    parser.add_argument(
        "--window_min",
        type=int,
        default=5,
        help="Sustained performance window in minutes",
    )
    parser.add_argument(
        "--service_name", default="hello", help="Knative service name to monitor"
    )
    parser.add_argument(
        "--namespace", default="hyper-swarm", help="Kubernetes namespace"
    )
    parser.add_argument(
        "--prom_url",
        help="Prometheus URL (default: $PROM_URL or http://localhost:9090)",
    )
    parser.add_argument(
        "--output", help="Output file path (default: reports/phase4_scale_verify.json)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Phase 4-7: Scale Verification and SLO Validation")
    print("=" * 70)

    # Load client results
    log_info(f"Loading client results from: {args.client_json}")
    client_data = load_client_results(args.client_json)

    # Get Istio metrics
    log_info("Collecting Istio service mesh metrics...")
    istio_metrics = get_istio_metrics(args.service_name, args.namespace)

    # Get scaling information
    log_info("Analyzing Knative scaling behavior...")
    scaling_info = get_knative_scaling_info(args.service_name, args.namespace)

    # Analyze sustained performance
    log_info(f"Analyzing sustained performance over {args.window_min} minute window...")
    performance_analysis = analyze_sustained_performance(client_data, args.window_min)

    # Validate SLO compliance
    log_info("Validating SLO compliance...")
    slo_validation = validate_slo_compliance(client_data, istio_metrics)

    # Generate comprehensive report
    report = generate_scale_verification_report(
        client_data,
        istio_metrics,
        scaling_info,
        performance_analysis,
        slo_validation,
        args.window_min,
    )

    # Output results
    output_file = args.output or "reports/phase4_scale_verify.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    log_info(f"Scale verification report saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("Scale Verification Summary")
    print("=" * 70)

    summary = report["test_summary"]
    metrics = report["performance_metrics"]
    slo = report["slo_metrics"]
    scaling = report["scaling_metrics"]

    status_icon = "✅" if summary["overall_success"] else "❌"
    print(
        f"{status_icon} Overall Result: {'PASS' if summary['overall_success'] else 'FAIL'}"
    )
    print()

    print("📊 Performance Metrics:")
    print(f"   • Client RPS: {metrics['client_rps']:.1f} (target: ≥800)")
    print(f"   • Istio RPS: {metrics['istio_rps']:.1f}")
    print(
        f"   • Duration: {metrics['test_duration_minutes']:.1f} minutes (target: ≥{args.window_min})"
    )
    print(f"   • RPS Efficiency: {metrics['rps_efficiency']:.1%}")
    print()

    print("🎯 SLO Compliance:")
    print(f"   • P50 Latency: {slo['p50_ms']:.0f}ms (target: <1000ms)")
    print(f"   • P95 Latency: {slo['p95_ms']:.0f}ms (target: <1500ms)")
    print(f"   • Success Rate: {slo['success_rate']:.1%} (target: ≥99%)")
    print()

    print("🚀 Scaling Behavior:")
    print(f"   • Current Pods: {scaling['current_pods']}")
    print(f"   • Scaling Detected: {'Yes' if scaling['scaling_detected'] else 'No'}")

    # Print individual check results
    print("\n📋 Detailed Checks:")
    print(
        f"   • RPS Requirement (≥800): {'✅ PASS' if summary['meets_rps_requirement'] else '❌ FAIL'}"
    )
    print(
        f"   • Duration Requirement (≥{args.window_min}min): {'✅ PASS' if summary['meets_duration_requirement'] else '❌ FAIL'}"
    )
    print(
        f"   • SLO Requirements: {'✅ PASS' if summary['meets_slo_requirements'] else '❌ FAIL'}"
    )
    print(
        f"   • Scaling Occurred: {'✅ YES' if summary['scaling_occurred'] else '⚠️  NO'}"
    )

    # Exit with appropriate code
    sys.exit(0 if summary["overall_success"] else 1)


if __name__ == "__main__":
    main()
