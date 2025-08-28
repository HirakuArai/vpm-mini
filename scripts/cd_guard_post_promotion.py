#!/usr/bin/env python3
"""
Phase 5-3: Post-Promotion SLO Guard
Monitor service SLO metrics after 100% promotion and trigger rollback if thresholds are breached
"""

import argparse
import json
import time
import statistics
import urllib.request
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Tuple


def probe_service(
    url: str, n: int = 300, timeout: float = 2.0, sleep: float = 0.05
) -> Tuple[float, int]:
    """
    Probe service endpoint to collect success rate and latency metrics.

    Args:
        url: Service endpoint URL
        n: Number of requests to make
        timeout: Request timeout in seconds
        sleep: Sleep between requests in seconds

    Returns:
        Tuple of (success_rate, median_latency_ms)
    """
    durations = []
    success_count = 0

    print(f"Probing {url} with {n} requests...")

    for i in range(n):
        start_time = time.time()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status_code = response.getcode()
        except Exception as e:
            status_code = 0
            print(f"Request {i+1} failed: {e}")

        duration_ms = int((time.time() - start_time) * 1000)
        durations.append(duration_ms)

        if status_code == 200:
            success_count += 1

        # Progress indicator for long-running probes
        if (i + 1) % 100 == 0:
            current_success_rate = success_count / (i + 1)
            print(
                f"  Progress: {i+1}/{n} requests, {current_success_rate:.1%} success rate"
            )

        time.sleep(sleep)

    success_rate = success_count / max(1, n)
    median_latency = int(statistics.median(durations)) if durations else 0

    return success_rate, median_latency


def monitor_window(
    url: str,
    window_minutes: int,
    batch_size: int,
    success_threshold: float,
    latency_threshold: int,
) -> Dict:
    """
    Monitor service over specified time window with periodic sampling.

    Args:
        url: Service endpoint URL
        window_minutes: Monitoring window duration in minutes
        batch_size: Number of requests per batch
        success_threshold: Minimum required success rate
        latency_threshold: Maximum allowed P50 latency in ms

    Returns:
        Dictionary with monitoring results
    """
    end_time = time.time() + window_minutes * 60
    samples = []

    print(f"Starting {window_minutes}-minute monitoring window...")
    print(
        f"Thresholds: success_rate >= {success_threshold:.1%}, p50 < {latency_threshold}ms"
    )

    batch_count = 0
    while time.time() < end_time:
        batch_count += 1
        remaining_time = int((end_time - time.time()) / 60)
        print(f"\nBatch {batch_count} (remaining: {remaining_time}m)")

        success_rate, p50_latency = probe_service(url, n=batch_size)

        sample = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success_rate": round(success_rate, 4),
            "p50_latency_ms": p50_latency,
            "batch_size": batch_size,
        }

        samples.append(sample)

        print(f"  Batch result: {success_rate:.1%} success, {p50_latency}ms p50")

        # Check if we should continue monitoring or exit early on severe failure
        if success_rate < 0.8:  # Emergency threshold
            print(
                "⚠️  Emergency threshold breached (success_rate < 80%), considering early exit..."
            )

        # Sleep between batches if we're not at the end of the window
        if time.time() < end_time:
            sleep_time = min(
                30, end_time - time.time()
            )  # Sleep up to 30s between batches
            if sleep_time > 0:
                print(f"  Sleeping {sleep_time:.0f}s before next batch...")
                time.sleep(sleep_time)

    # Calculate aggregate metrics
    if not samples:
        return {
            "window_min": window_minutes,
            "success_rate": 0.0,
            "p50_ms": 0,
            "guard_ok": False,
            "samples": [],
            "error": "No samples collected",
        }

    success_rates = [s["success_rate"] for s in samples]
    p50_latencies = [s["p50_latency_ms"] for s in samples]

    median_success_rate = round(statistics.median(success_rates), 4)
    median_p50_latency = int(statistics.median(p50_latencies))

    # Determine if guard conditions are met
    guard_ok = (median_success_rate >= success_threshold) and (
        median_p50_latency < latency_threshold
    )

    result = {
        "window_min": window_minutes,
        "success_rate": median_success_rate,
        "p50_ms": median_p50_latency,
        "guard_ok": guard_ok,
        "samples": samples,
        "thresholds": {
            "success_rate_min": success_threshold,
            "p50_latency_max_ms": latency_threshold,
        },
        "statistics": {
            "total_batches": len(samples),
            "min_success_rate": min(success_rates),
            "max_success_rate": max(success_rates),
            "min_p50_ms": min(p50_latencies),
            "max_p50_ms": max(p50_latencies),
        },
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Post-promotion SLO guard monitoring")
    parser.add_argument(
        "--url",
        default=os.environ.get("URL", "http://localhost:31380/hello"),
        help="Service endpoint URL to monitor",
    )
    parser.add_argument(
        "--window_min",
        type=int,
        default=int(os.environ.get("GUARD_WINDOW_MIN", "10")),
        help="Monitoring window duration in minutes",
    )
    parser.add_argument(
        "--batch_n",
        type=int,
        default=int(os.environ.get("GUARD_BATCH_N", "300")),
        help="Number of requests per monitoring batch",
    )
    parser.add_argument(
        "--succ_min",
        type=float,
        default=float(os.environ.get("GUARD_SUCC_MIN", "0.99")),
        help="Minimum required success rate",
    )
    parser.add_argument(
        "--p50_max",
        type=int,
        default=int(os.environ.get("GUARD_P50_MAX", "1000")),
        help="Maximum allowed P50 latency in milliseconds",
    )
    parser.add_argument(
        "--out",
        default="reports/phase5_cd_guard_result.json",
        help="Output file for monitoring results",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print("Post-Promotion SLO Guard Configuration:")
        print(f"  URL: {args.url}")
        print(f"  Window: {args.window_min} minutes")
        print(f"  Batch size: {args.batch_n} requests")
        print(f"  Success threshold: {args.succ_min:.1%}")
        print(f"  Latency threshold: {args.p50_max}ms")
        print(f"  Output: {args.out}")
        print()

    try:
        # Run monitoring window
        result = monitor_window(
            url=args.url,
            window_minutes=args.window_min,
            batch_size=args.batch_n,
            success_threshold=args.succ_min,
            latency_threshold=args.p50_max,
        )

        # Add metadata
        result.update(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "config": {
                    "url": args.url,
                    "window_min": args.window_min,
                    "batch_n": args.batch_n,
                    "succ_min": args.succ_min,
                    "p50_max": args.p50_max,
                },
            }
        )

        # Print summary
        print("\n" + "=" * 60)
        print("POST-PROMOTION SLO GUARD RESULTS")
        print("=" * 60)
        print(f"Monitoring window: {result['window_min']} minutes")
        print(
            f"Success rate: {result['success_rate']:.1%} (threshold: {args.succ_min:.1%})"
        )
        print(f"P50 latency: {result['p50_ms']}ms (threshold: {args.p50_max}ms)")
        print(f"Guard result: {'✅ PASS' if result['guard_ok'] else '❌ FAIL'}")

        if not result["guard_ok"]:
            print("\n⚠️  SLO GUARD FAILURE DETECTED ⚠️")
            print("Automatic rollback will be triggered...")

            # Add failure details
            if result["success_rate"] < args.succ_min:
                print(
                    f"  - Success rate {result['success_rate']:.1%} < {args.succ_min:.1%}"
                )
            if result["p50_ms"] >= args.p50_max:
                print(f"  - P50 latency {result['p50_ms']}ms >= {args.p50_max}ms")
        else:
            print("\n✅ SLO guard passed - promotion stable")

        # Save results
        os.makedirs("reports", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)

        if args.verbose:
            print(f"\nResults saved to: {args.out}")
            print("\nFull result:")
            print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result["guard_ok"] else 1)

    except Exception as e:
        error_result = {
            "window_min": args.window_min,
            "success_rate": 0.0,
            "p50_ms": 0,
            "guard_ok": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "url": args.url,
                "window_min": args.window_min,
                "batch_n": args.batch_n,
                "succ_min": args.succ_min,
                "p50_max": args.p50_max,
            },
        }

        print(f"❌ Error during monitoring: {e}")

        # Save error result
        os.makedirs("reports", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(error_result, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
