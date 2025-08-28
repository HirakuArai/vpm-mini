#!/usr/bin/env python3

import asyncio
import aiohttp
import argparse
import time
import json
import sys
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class RequestResult:
    timestamp: float
    status_code: int
    response_time_ms: float
    error: str = None


@dataclass
class LoadTestResults:
    total_requests: int
    total_duration_s: float
    success_rate: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    errors: Dict[str, int]


class ChaosLoadGenerator:
    def __init__(self, url: str, rps: int = 10, duration: int = 60, timeout: int = 30):
        self.url = url
        self.rps = rps
        self.duration = duration
        self.timeout = timeout
        self.results: List[RequestResult] = []

    async def make_request(
        self, session: aiohttp.ClientSession, request_id: int
    ) -> RequestResult:
        """Make a single HTTP request and record metrics"""
        start_time = time.time()
        timestamp = start_time

        try:
            async with session.get(
                self.url, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                # Read response body to ensure complete request
                await response.read()
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000

                return RequestResult(
                    timestamp=timestamp,
                    status_code=response.status,
                    response_time_ms=response_time_ms,
                )

        except asyncio.TimeoutError:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            return RequestResult(
                timestamp=timestamp,
                status_code=0,
                response_time_ms=response_time_ms,
                error="timeout",
            )
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            return RequestResult(
                timestamp=timestamp,
                status_code=0,
                response_time_ms=response_time_ms,
                error=str(e),
            )

    async def run_load_test(self) -> LoadTestResults:
        """Execute the load test with specified RPS and duration"""
        print(
            f"🔥 Starting load test: {self.rps} RPS for {self.duration}s against {self.url}"
        )

        # Calculate request intervals
        interval = 1.0 / self.rps
        total_requests = self.rps * self.duration

        start_time = time.time()
        request_tasks = []

        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        async with aiohttp.ClientSession(connector=connector) as session:

            # Schedule requests at specified intervals
            for i in range(total_requests):
                if i > 0:
                    # Wait for the next request interval
                    await asyncio.sleep(interval)

                # Check if we've exceeded our duration
                elapsed = time.time() - start_time
                if elapsed >= self.duration:
                    break

                # Create request task
                task = asyncio.create_task(self.make_request(session, i))
                request_tasks.append(task)

                # Print progress every 50 requests
                if (i + 1) % 50 == 0:
                    print(
                        f"  📤 Sent {i + 1}/{total_requests} requests ({elapsed:.1f}s elapsed)"
                    )

            # Wait for all requests to complete
            print("⏳ Waiting for all requests to complete...")
            self.results = await asyncio.gather(*request_tasks)

        total_duration = time.time() - start_time
        return self.calculate_metrics(total_duration)

    def calculate_metrics(self, total_duration: float) -> LoadTestResults:
        """Calculate load test metrics from results"""
        if not self.results:
            raise ValueError("No results to calculate metrics from")

        # Basic counts
        total_requests = len(self.results)
        successful_requests = [r for r in self.results if 200 <= r.status_code < 300]
        success_rate = len(successful_requests) / total_requests

        # Response time metrics
        response_times = [r.response_time_ms for r in self.results]
        response_times.sort()

        avg_response_time = sum(response_times) / len(response_times)

        # Percentiles
        def percentile(data: List[float], p: float) -> float:
            index = int((len(data) - 1) * p / 100)
            return data[index]

        p50 = percentile(response_times, 50)
        p95 = percentile(response_times, 95)
        p99 = percentile(response_times, 99)

        # Error analysis
        error_counts = {}
        for result in self.results:
            if result.error:
                error_counts[result.error] = error_counts.get(result.error, 0) + 1
            elif result.status_code >= 400:
                error_key = f"http_{result.status_code}"
                error_counts[error_key] = error_counts.get(error_key, 0) + 1

        # Calculate actual RPS
        actual_rps = total_requests / total_duration

        return LoadTestResults(
            total_requests=total_requests,
            total_duration_s=total_duration,
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            requests_per_second=actual_rps,
            errors=error_counts,
        )

    def print_results(self, results: LoadTestResults):
        """Print human-readable load test results"""
        print("\n" + "=" * 60)
        print("🎯 CHAOS LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Requests:      {results.total_requests:,}")
        print(f"Duration:           {results.total_duration_s:.2f}s")
        print(f"Requests/Second:    {results.requests_per_second:.2f}")
        print(f"Success Rate:       {results.success_rate:.1%}")
        print()
        print("Response Times:")
        print(f"  Average:          {results.avg_response_time_ms:.1f}ms")
        print(f"  50th percentile:  {results.p50_response_time_ms:.1f}ms")
        print(f"  95th percentile:  {results.p95_response_time_ms:.1f}ms")
        print(f"  99th percentile:  {results.p99_response_time_ms:.1f}ms")

        if results.errors:
            print("\nErrors:")
            for error, count in results.errors.items():
                print(f"  {error}: {count}")

        print("=" * 60)

    def save_results(self, results: LoadTestResults, filename: str):
        """Save results to JSON file"""
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_config": {
                "url": self.url,
                "target_rps": self.rps,
                "duration_s": self.duration,
                "timeout_s": self.timeout,
            },
            "results": asdict(results),
        }

        with open(filename, "w") as f:
            json.dump(output, f, indent=2)

        print(f"💾 Results saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Chaos Load Generator for SLO Verification"
    )
    parser.add_argument("--url", required=True, help="Target URL to test")
    parser.add_argument(
        "--rps", type=int, default=20, help="Requests per second (default: 20)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=180,
        help="Test duration in seconds (default: 180)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--output", help="Output JSON file (default: loadtest_results.json)"
    )

    args = parser.parse_args()

    # Set default output filename if not specified
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"loadtest_results_{timestamp}.json"

    try:
        # Create and run load generator
        generator = ChaosLoadGenerator(
            url=args.url, rps=args.rps, duration=args.duration, timeout=args.timeout
        )

        # Run the test
        results = asyncio.run(generator.run_load_test())

        # Display and save results
        generator.print_results(results)
        generator.save_results(results, args.output)

        # Exit with non-zero code if success rate is too low
        if results.success_rate < 0.95:
            print(f"⚠️  Warning: Success rate {results.success_rate:.1%} is below 95%")
            sys.exit(1)
        else:
            print("✅ Load test completed successfully")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n🛑 Load test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
