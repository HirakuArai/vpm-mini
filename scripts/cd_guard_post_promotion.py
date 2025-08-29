#!/usr/bin/env python3

import requests
import time
import json
import argparse
import sys
from statistics import mean
from datetime import datetime


def monitor_service(url, duration_min=10, success_threshold=0.99, p50_threshold=1000):
    """
    Monitor service post-promotion for specified duration
    Returns guard_ok status based on SLO thresholds
    """
    print("Starting post-promotion guard monitoring...")
    print(f"Duration: {duration_min} minutes")
    print(f"Success threshold: {success_threshold*100}%")
    print(f"P50 latency threshold: {p50_threshold}ms")
    print()

    start_time = time.time()
    end_time = start_time + (duration_min * 60)

    response_times = []
    success_count = 0
    total_requests = 0

    while time.time() < end_time:
        try:
            req_start = time.time()
            resp = requests.get(url, timeout=5)
            req_duration = (time.time() - req_start) * 1000
            response_times.append(req_duration)
            total_requests += 1

            if resp.status_code < 400:
                success_count += 1

        except Exception:
            response_times.append(5000)  # Timeout penalty
            total_requests += 1

        # Progress update every 30 seconds
        if total_requests % 30 == 0:
            elapsed = time.time() - start_time
            remaining = (end_time - time.time()) / 60
            current_success_rate = (
                success_count / total_requests if total_requests > 0 else 0
            )
            print(
                f"Progress: {elapsed/60:.1f}m elapsed, {remaining:.1f}m remaining, SR: {current_success_rate:.3f}"
            )

        time.sleep(1)  # 1 RPS

    # Calculate final metrics
    final_success_rate = success_count / total_requests if total_requests > 0 else 0
    final_p50 = (
        sorted(response_times)[len(response_times) // 2] if response_times else 0
    )
    final_avg = mean(response_times) if response_times else 0

    # Guard decision
    guard_ok = final_success_rate >= success_threshold and final_p50 <= p50_threshold

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "monitoring_duration_min": duration_min,
        "total_requests": total_requests,
        "success_count": success_count,
        "success_rate": final_success_rate,
        "avg_latency_ms": final_avg,
        "p50_latency_ms": final_p50,
        "success_threshold": success_threshold,
        "p50_threshold": p50_threshold,
        "guard_ok": guard_ok,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Post-promotion guard monitoring")
    parser.add_argument(
        "--url", default="http://localhost:31380", help="Service URL to monitor"
    )
    parser.add_argument(
        "--out", default="reports/phase5_cd_guard_result.json", help="Output JSON file"
    )

    args = parser.parse_args()

    import os

    # Get environment variables with defaults
    duration_min = float(os.environ.get("GUARD_WINDOW_MIN", "10"))
    success_threshold = float(os.environ.get("GUARD_SUCC_MIN", "0.99"))
    p50_threshold = float(os.environ.get("GUARD_P50_MAX", "1000"))

    print("========================================")
    print("Post-Promotion Guard Monitoring")
    print("========================================")

    try:
        result = monitor_service(
            args.url, duration_min, success_threshold, p50_threshold
        )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(args.out), exist_ok=True)

        # Save result
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)

        print("\nResults:")
        print(f"  Total requests: {result['total_requests']}")
        print(f"  Success rate: {result['success_rate']:.3f}")
        print(f"  P50 latency: {result['p50_latency_ms']:.1f}ms")
        print(f"  Guard OK: {result['guard_ok']}")
        print(f"  Results saved to: {args.out}")

        if result["guard_ok"]:
            print("\n✅ Post-promotion guard PASSED")
            sys.exit(0)
        else:
            print("\n❌ Post-promotion guard FAILED")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Monitoring interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
