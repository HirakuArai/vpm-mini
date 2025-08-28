#!/usr/bin/env python3
"""
Phase 4-6: SLO Gate Validation for Canary Promotion

Validates Service Level Objectives (SLOs) at each promotion stage:
- Performance: P50 latency < 1000ms
- Reliability: Success rate ≥ 99%
- Final stage: V2 share ≥ 95% (for 100:0 stage)
"""

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError


def log_info(message):
    print(f"\033[32m[INFO]\033[0m {message}")


def log_warn(message):
    print(f"\033[33m[WARN]\033[0m {message}")


def log_error(message):
    print(f"\033[31m[ERROR]\033[0m {message}")


def perform_load_test(url, num_requests=300, timeout=2.0, request_interval=0.01):
    """
    Perform load test against the canary endpoint.

    Returns:
        dict: Test results with success_rate, p50_ms, v2_share
    """
    log_info(f"Starting load test: {num_requests} requests to {url}")

    durations = []
    successful_requests = 0
    v2_responses = 0
    error_count = 0

    for i in range(num_requests):
        if (i + 1) % 100 == 0:
            log_info(f"Progress: {i + 1}/{num_requests} requests")

        start_time = time.time()

        try:
            with urlopen(url, timeout=timeout) as response:
                body = response.read().decode("utf-8", "ignore")
                status_code = response.getcode()

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            durations.append(duration_ms)

            if status_code == 200:
                successful_requests += 1
                # Check if response is from v2 service
                if "v2" in body or "TARGET=v2" in body:
                    v2_responses += 1
            else:
                error_count += 1

        except (URLError, OSError):
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            durations.append(duration_ms)
            error_count += 1

        # Brief pause to avoid overwhelming the service
        time.sleep(request_interval)

    # Calculate metrics
    success_rate = successful_requests / num_requests
    v2_share = v2_responses / num_requests
    p50_ms = int(statistics.median(durations)) if durations else 0

    results = {
        "total_requests": num_requests,
        "successful_requests": successful_requests,
        "v2_responses": v2_responses,
        "error_count": error_count,
        "success_rate": round(success_rate, 3),
        "p50_ms": p50_ms,
        "v2_share": round(v2_share, 3),
    }

    log_info("Load test results:")
    log_info(f"  Total requests: {num_requests}")
    log_info(f"  Successful requests: {successful_requests}")
    log_info(f"  V2 responses: {v2_responses}")
    log_info(f"  Error count: {error_count}")
    log_info(f"  Success rate: {success_rate:.3f} ({success_rate * 100:.1f}%)")
    log_info(f"  V2 share: {v2_share:.3f} ({v2_share * 100:.1f}%)")
    log_info(f"  P50 latency: {p50_ms}ms")

    return results


def validate_slo_gates(results, stage):
    """
    Validate SLO gates based on stage and results.

    Args:
        results (dict): Load test results
        stage (str): Current stage (e.g., "90:10", "50:50", "100:0")

    Returns:
        tuple: (gate_ok, final_ok, validation_details)
    """
    hello_weight, v2_weight = map(int, stage.split(":"))

    # Standard SLO gates
    p50_gate = results["p50_ms"] < 1000
    success_rate_gate = results["success_rate"] >= 0.99
    gate_ok = p50_gate and success_rate_gate

    # Stage-specific validations
    final_ok = True
    validation_details = {
        "p50_gate": {
            "threshold": 1000,
            "actual": results["p50_ms"],
            "passed": p50_gate,
        },
        "success_rate_gate": {
            "threshold": 0.99,
            "actual": results["success_rate"],
            "passed": success_rate_gate,
        },
    }

    if stage == "100:0":
        # Final stage: ensure v2 is getting almost all traffic
        v2_share_gate = results["v2_share"] >= 0.95
        final_ok = v2_share_gate
        validation_details["v2_share_gate"] = {
            "threshold": 0.95,
            "actual": results["v2_share"],
            "passed": v2_share_gate,
        }
    elif stage == "50:50":
        # Middle stage: expect roughly balanced traffic
        v2_share_balanced = 0.4 <= results["v2_share"] <= 0.6
        validation_details["v2_share_balanced"] = {
            "range": [0.4, 0.6],
            "actual": results["v2_share"],
            "passed": v2_share_balanced,
        }
    elif stage == "90:10":
        # Initial stage: expect low v2 traffic
        v2_share_low = 0.05 <= results["v2_share"] <= 0.20
        validation_details["v2_share_low"] = {
            "range": [0.05, 0.20],
            "actual": results["v2_share"],
            "passed": v2_share_low,
        }

    return gate_ok, final_ok, validation_details


def update_promotion_results(
    output_file, stage, results, gate_ok, final_ok, validation_details
):
    """Update promotion results file with stage results."""
    try:
        if Path(output_file).exists():
            with open(output_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
    except (json.JSONDecodeError, OSError):
        data = {}

    # Ensure stages object exists
    if "stages" not in data:
        data["stages"] = {}

    # Add stage results
    stage_data = {
        **results,
        "gate_ok": gate_ok,
        "final_ok": final_ok,
        "validation": validation_details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    data["stages"][stage] = stage_data

    # Update overall status
    all_gates_passed = all(
        stage_result.get("gate_ok", False) and stage_result.get("final_ok", False)
        for stage_result in data["stages"].values()
    )
    data["all_gates_passed"] = all_gates_passed

    # Write updated results
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="SLO Gate Validation for Canary Promotion"
    )
    parser.add_argument("--url", required=True, help="URL to test")
    parser.add_argument(
        "--stage", required=True, help="Current stage (e.g., '90:10', '50:50', '100:0')"
    )
    parser.add_argument("--n", type=int, default=300, help="Number of requests")
    parser.add_argument("--out", required=True, help="Output JSON file for results")
    parser.add_argument(
        "--timeout", type=float, default=2.0, help="Request timeout in seconds"
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"SLO Gate Validation - Stage: {args.stage}")
    print("=" * 60)

    # Perform load test
    results = perform_load_test(args.url, args.n, args.timeout)

    # Validate SLO gates
    gate_ok, final_ok, validation_details = validate_slo_gates(results, args.stage)

    # Update promotion results file
    update_promotion_results(
        args.out, args.stage, results, gate_ok, final_ok, validation_details
    )

    # Print stage results
    stage_result = {
        **results,
        "gate_ok": gate_ok,
        "final_ok": final_ok,
        "validation": validation_details,
    }

    print("\n" + "=" * 60)
    print("Stage Validation Results")
    print("=" * 60)
    print(json.dumps(stage_result, indent=2))

    # Summary
    overall_success = gate_ok and final_ok

    if overall_success:
        log_info(f"✅ Stage {args.stage} validation PASSED")
        if validation_details.get("p50_gate", {}).get("passed"):
            log_info(f"   - Performance: P50 {results['p50_ms']}ms < 1000ms")
        if validation_details.get("success_rate_gate", {}).get("passed"):
            log_info(f"   - Reliability: {results['success_rate']:.1%} ≥ 99%")
        if "v2_share_gate" in validation_details:
            if validation_details["v2_share_gate"]["passed"]:
                log_info(f"   - Final traffic: {results['v2_share']:.1%} ≥ 95%")
    else:
        log_error(f"❌ Stage {args.stage} validation FAILED")
        if not validation_details.get("p50_gate", {}).get("passed"):
            log_error(f"   - Performance gate: P50 {results['p50_ms']}ms ≥ 1000ms")
        if not validation_details.get("success_rate_gate", {}).get("passed"):
            log_error(f"   - Reliability gate: {results['success_rate']:.1%} < 99%")
        if (
            "v2_share_gate" in validation_details
            and not validation_details["v2_share_gate"]["passed"]
        ):
            log_error(f"   - Final traffic gate: {results['v2_share']:.1%} < 95%")

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
