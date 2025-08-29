#!/usr/bin/env python3
"""
Phase 4-7: High Load Generator (800 RPS Sustained)

Async HTTP load generator with precise RPS control and comprehensive metrics.
Supports sustained high load testing with configurable concurrency and duration.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from typing import Dict, List, Optional

import aiohttp


class LoadStats:
    """Thread-safe statistics collector for load testing."""

    def __init__(self):
        self.codes: Dict[str, int] = {}
        self.latencies_ms: List[int] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_requests = 0
        self.successful_requests = 0
        self.lock = asyncio.Lock()

    async def record_response(self, status_code: int, latency_ms: int):
        """Record a response with status code and latency."""
        async with self.lock:
            code_str = str(status_code)
            self.codes[code_str] = self.codes.get(code_str, 0) + 1
            self.latencies_ms.append(latency_ms)
            self.total_requests += 1
            if status_code == 200:
                self.successful_requests += 1

    async def get_summary(self) -> Dict:
        """Get comprehensive statistics summary."""
        async with self.lock:
            if not self.latencies_ms:
                return {
                    "error": "No requests completed",
                    "total_requests": 0,
                    "success_rate": 0.0,
                    "effective_rps": 0.0,
                }

            duration_s = (self.end_time or time.time()) - (
                self.start_time or time.time()
            )
            effective_rps = round(self.total_requests / max(1, duration_s), 1)
            success_rate = round(
                self.successful_requests / max(1, self.total_requests), 4
            )

            p50_ms = int(statistics.median(self.latencies_ms))
            p95_ms = (
                int(statistics.quantiles(self.latencies_ms, n=20)[18])
                if len(self.latencies_ms) >= 20
                else p50_ms
            )
            p99_ms = (
                int(statistics.quantiles(self.latencies_ms, n=100)[98])
                if len(self.latencies_ms) >= 100
                else p95_ms
            )

            return {
                "rps_target": getattr(self, "target_rps", 0),
                "rps_effective": effective_rps,
                "duration_s": round(duration_s, 1),
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "success_rate": success_rate,
                "latency_stats": {
                    "p50_ms": p50_ms,
                    "p95_ms": p95_ms,
                    "p99_ms": p99_ms,
                    "min_ms": min(self.latencies_ms),
                    "max_ms": max(self.latencies_ms),
                },
                "status_codes": dict(self.codes),
                "slo_metrics": {
                    "meets_rps_target": effective_rps
                    >= getattr(self, "target_rps", 0) * 0.95,
                    "meets_success_rate": success_rate >= 0.99,
                    "meets_p50_latency": p50_ms < 1000,
                    "meets_p95_latency": p95_ms < 1500,
                },
            }


async def make_request(
    session: aiohttp.ClientSession, url: str, timeout: float, stats: LoadStats
) -> None:
    """Make a single HTTP request and record statistics."""
    start_time = time.time()

    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            # Read response body to ensure complete request
            await response.text()
            status_code = response.status
    except asyncio.TimeoutError:
        status_code = 408  # Request Timeout
    except aiohttp.ClientError:
        status_code = 500  # Server Error
    except Exception:
        status_code = 0  # Unknown Error

    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    await stats.record_response(status_code, latency_ms)


async def ramp_up_phase(
    session: aiohttp.ClientSession,
    url: str,
    target_rps: int,
    timeout: float,
    stats: LoadStats,
    ramp_duration: int = 60,
) -> None:
    """Gradual ramp-up to target RPS to avoid overwhelming the service."""
    print(f"🚀 Ramp-up phase: 0 → {target_rps} RPS over {ramp_duration}s")

    ramp_start = time.time()
    semaphore = asyncio.Semaphore(min(target_rps, 500))  # Limit concurrent requests

    while time.time() - ramp_start < ramp_duration:
        elapsed = time.time() - ramp_start
        progress = elapsed / ramp_duration
        current_rps = int(target_rps * progress)

        if current_rps > 0:
            interval = 1.0 / current_rps

            async def bounded_request():
                async with semaphore:
                    await make_request(session, url, timeout, stats)

            # Schedule requests at current RPS
            request_start = time.time()
            asyncio.create_task(bounded_request())

            # Maintain precise timing
            sleep_time = max(0, interval - (time.time() - request_start))
            await asyncio.sleep(sleep_time)
        else:
            await asyncio.sleep(0.1)

    print(f"✅ Ramp-up complete: reached {target_rps} RPS")


async def sustained_load_phase(
    session: aiohttp.ClientSession,
    url: str,
    rps: int,
    duration_s: int,
    timeout: float,
    concurrency: int,
    stats: LoadStats,
) -> None:
    """Execute sustained load at target RPS for specified duration."""
    print(
        f"🎯 Sustained load: {rps} RPS for {duration_s}s (concurrency: {concurrency})"
    )

    semaphore = asyncio.Semaphore(concurrency)
    interval = 1.0 / rps

    phase_start = time.time()
    request_count = 0

    while time.time() - phase_start < duration_s:
        loop_start = time.time()

        async def bounded_request():
            async with semaphore:
                await make_request(session, url, timeout, stats)

        # Schedule request
        asyncio.create_task(bounded_request())
        request_count += 1

        # Progress reporting every 10 seconds
        if request_count % (rps * 10) == 0:
            elapsed = time.time() - phase_start
            current_rps = round(request_count / elapsed, 1)
            print(
                f"📊 Progress: {elapsed:.0f}s elapsed, {request_count} requests, {current_rps} RPS"
            )

        # Maintain precise RPS timing
        sleep_time = max(0, interval - (time.time() - loop_start))
        await asyncio.sleep(sleep_time)

    print(
        f"⏱️  Sustained phase complete: {request_count} requests in {time.time() - phase_start:.1f}s"
    )


async def cooldown_phase(session: aiohttp.ClientSession, timeout: float) -> None:
    """Wait for all outstanding requests to complete."""
    print("❄️  Cooldown phase: waiting for outstanding requests...")
    await asyncio.sleep(timeout + 2)  # Wait for timeout + buffer
    print("✅ Cooldown complete")


async def bombard(
    url: str,
    rps: int,
    duration_s: int,
    timeout: float = 2.0,
    concurrency: int = 200,
    enable_ramp_up: bool = True,
) -> Dict:
    """
    Main load testing function with ramp-up, sustained load, and cooldown phases.

    Args:
        url: Target URL for load testing
        rps: Target requests per second
        duration_s: Duration of sustained load phase
        timeout: Request timeout in seconds
        concurrency: Maximum concurrent requests
        enable_ramp_up: Whether to include ramp-up phase

    Returns:
        Dictionary containing comprehensive load test results
    """
    stats = LoadStats()
    stats.target_rps = rps
    stats.start_time = time.time()

    # Configure aiohttp session with optimized settings
    connector = aiohttp.TCPConnector(
        limit=concurrency * 2,
        limit_per_host=concurrency * 2,
        keepalive_timeout=30,
        enable_cleanup_closed=True,
    )

    timeout_config = aiohttp.ClientTimeout(total=timeout)

    try:
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers={"User-Agent": "Phase4-LoadBombard/1.0"},
        ) as session:

            print(f"🎯 Starting load test: {url}")
            print(
                f"📋 Parameters: {rps} RPS × {duration_s}s, concurrency={concurrency}, timeout={timeout}s"
            )

            # Phase 1: Ramp-up (optional)
            if enable_ramp_up and rps > 100:
                ramp_duration = min(60, duration_s // 10)  # 10% of duration, max 60s
                await ramp_up_phase(session, url, rps, timeout, stats, ramp_duration)

            # Phase 2: Sustained load
            await sustained_load_phase(
                session, url, rps, duration_s, timeout, concurrency, stats
            )

            # Phase 3: Cooldown
            await cooldown_phase(session, timeout)

    finally:
        stats.end_time = time.time()
        await connector.close()

    # Generate final report
    summary = await stats.get_summary()

    # Add test configuration to summary
    summary.update(
        {
            "test_config": {
                "url": url,
                "target_rps": rps,
                "duration_s": duration_s,
                "timeout_s": timeout,
                "concurrency": concurrency,
                "ramp_up_enabled": enable_ramp_up,
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4-7: High-performance async load generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic 800 RPS test for 10 minutes
  python3 phase4_load_bombard.py --url http://localhost:31380/hello --rps 800 --duration 600

  # High concurrency test with custom timeout
  python3 phase4_load_bombard.py --url http://localhost:31380/hello --rps 1200 --duration 300 --concurrency 500 --timeout 3.0

  # Quick test without ramp-up
  python3 phase4_load_bombard.py --url http://localhost:31380/hello --rps 100 --duration 60 --no-ramp-up
        """,
    )

    parser.add_argument("--url", required=True, help="Target URL for load testing")
    parser.add_argument(
        "--rps", type=int, default=800, help="Target requests per second"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Duration in seconds (default: 10 minutes)",
    )
    parser.add_argument(
        "--timeout", type=float, default=2.0, help="Request timeout in seconds"
    )
    parser.add_argument(
        "--concurrency", type=int, default=200, help="Maximum concurrent requests"
    )
    parser.add_argument("--no-ramp-up", action="store_true", help="Skip ramp-up phase")
    parser.add_argument("--output", help="Output file for results (default: stdout)")

    args = parser.parse_args()

    # Validation
    if args.rps <= 0:
        print("❌ Error: RPS must be positive")
        sys.exit(1)

    if args.duration <= 0:
        print("❌ Error: Duration must be positive")
        sys.exit(1)

    if args.concurrency <= 0:
        print("❌ Error: Concurrency must be positive")
        sys.exit(1)

    # Run load test
    try:
        results = asyncio.run(
            bombard(
                url=args.url,
                rps=args.rps,
                duration_s=args.duration,
                timeout=args.timeout,
                concurrency=args.concurrency,
                enable_ramp_up=not args.no_ramp_up,
            )
        )

        # Output results
        results_json = json.dumps(results, indent=2)

        if args.output:
            with open(args.output, "w") as f:
                f.write(results_json)
            print(f"📁 Results saved to: {args.output}")
        else:
            print(results_json)

        # Exit code based on SLO compliance
        slo_metrics = results.get("slo_metrics", {})
        all_slos_met = all(
            [
                slo_metrics.get("meets_success_rate", False),
                slo_metrics.get("meets_p50_latency", False),
            ]
        )

        if all_slos_met:
            print("✅ Load test completed successfully - All SLOs met")
            sys.exit(0)
        else:
            print("⚠️  Load test completed with SLO violations")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Load test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
