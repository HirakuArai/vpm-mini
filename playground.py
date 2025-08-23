import sys
import argparse


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
        "--hello", action="store_true", help="Print hello message and exit"
    )
    parser.add_argument("input", nargs="?", default="hello", help="Input text")
    args = parser.parse_args()

    if args.hello:
        print(f"[hello] role={args.role}")
        sys.exit(0)

    run_once(args.input)


if __name__ == "__main__":
    main()
