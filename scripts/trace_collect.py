#!/usr/bin/env python3
import os
import re
import sys
from collections import defaultdict


def collect_traces(log_file):
    """Collect trace logs from a single log file."""
    traces = defaultdict(list)

    if not os.path.exists(log_file):
        return traces

    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            # Look for trace_id patterns in logs
            trace_match = re.search(r"trace_id=([a-zA-Z0-9-]+)", line)
            if trace_match:
                trace_id = trace_match.group(1)
                traces[trace_id].append(line)

    return traces


def summarize_traces(traces):
    """Summarize trace information."""
    summary = []

    for trace_id, logs in traces.items():
        roles = set()
        redis_checks = 0
        hello_messages = 0

        for log in logs:
            if "[hello]" in log:
                role_match = re.search(r"role=(\w+)", log)
                if role_match:
                    roles.add(role_match.group(1))
                    hello_messages += 1
            if "[redis] ok" in log:
                redis_checks += 1

        summary.append(
            {
                "trace_id": trace_id,
                "roles": sorted(roles),
                "hello_messages": hello_messages,
                "redis_checks": redis_checks,
                "total_logs": len(logs),
            }
        )

    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/trace_collect.py <log_file> [log_file2 ...]")
        sys.exit(1)

    all_traces = defaultdict(list)

    # Collect traces from all provided log files
    for log_file in sys.argv[1:]:
        traces = collect_traces(log_file)
        for trace_id, logs in traces.items():
            all_traces[trace_id].extend(logs)

    # Generate summary
    summary = summarize_traces(all_traces)

    print("=== Trace Collection Summary ===")
    print(f"Total unique traces: {len(summary)}")
    print()

    for trace_info in summary:
        print(f"Trace ID: {trace_info['trace_id']}")
        print(f"  Roles: {', '.join(trace_info['roles'])}")
        print(f"  Hello messages: {trace_info['hello_messages']}")
        print(f"  Redis checks: {trace_info['redis_checks']}")
        print(f"  Total logs: {trace_info['total_logs']}")
        print()

    # Show detailed logs for each trace
    print("=== Detailed Logs ===")
    for trace_id, logs in all_traces.items():
        print(f"\nTrace ID: {trace_id}")
        for log in logs:
            print(f"  {log}")


if __name__ == "__main__":
    main()
