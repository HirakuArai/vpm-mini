import sys
import argparse
import time
import os
from src.utils.metrics import observe


def run_once(input_text: str):
    """Run through all 5 roles with validation."""
    from src.roles.watcher import Watcher
    from src.roles.curator import Curator
    from src.roles.planner import Planner
    from src.roles.synthesizer import Synthesizer
    from src.roles.archivist import Archivist

    payload = {"input": input_text}

    try:
        for role_cls in [Watcher, Curator, Planner, Synthesizer, Archivist]:
            role = role_cls()
            payload = role.run(payload)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    print("All roles completed successfully")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="watcher", help="Role name")
    parser.add_argument(
        "--trace-id", dest="trace_id", help="Trace ID for cross-role tracking"
    )
    parser.add_argument(
        "--hello", action="store_true", help="Print hello message and exit"
    )
    parser.add_argument("--healthz", action="store_true")
    parser.add_argument("--metrics", action="store_true")
    parser.add_argument("input", nargs="?", default="hello", help="Input text")
    args = parser.parse_args()

    # Handle trace_id generation and propagation
    trace_id = args.trace_id or os.getenv("TRACE_ID")
    if not trace_id:
        from src.utils.trace import new_trace_id

        trace_id = new_trace_id()
    os.environ["TRACE_ID"] = trace_id

    if args.metrics:
        from wsgiref.simple_server import make_server
        from src.utils.metrics import render_metrics

        with make_server(
            "", int(os.getenv("METRICS_PORT", "9000")), render_metrics
        ) as httpd:
            httpd.serve_forever()
        return

    if args.healthz:
        from src.utils.healthz import serve

        serve()
        return

    if args.metrics:
        from src.utils.metrics import serve_metrics

        serve_metrics()
        return

    if args.hello:
        _t = time.time()
        role = args.role
        ok = True
        print(f"[hello] role={args.role} trace_id={os.getenv('TRACE_ID')}")
        observe(role, ok, _t)
        try:
            import shlex
            import subprocess

            host = os.getenv("REDIS_HOST")
            if host:
                subprocess.check_call(
                    shlex.split(f"redis-cli -h {host} ping"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"[redis] ok trace_id={os.getenv('TRACE_ID')}")
        except Exception as e:
            print("[redis] check failed:", e, file=sys.stderr)
        sys.exit(0)

    run_once(args.input)


if __name__ == "__main__":
    main()
