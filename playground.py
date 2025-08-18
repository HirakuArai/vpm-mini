import sys
from src.roles.watcher import Watcher
from src.roles.curator import Curator
from src.roles.planner import Planner
from src.roles.synthesizer import Synthesizer
from src.roles.archivist import Archivist


def run_once(input_text: str):
    """Run through all 5 roles with validation."""
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


if __name__ == "__main__":
    input_text = sys.argv[1] if len(sys.argv) > 1 else "hello"
    run_once(input_text)
