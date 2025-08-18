from src.roles.watcher import Watcher
from src.roles.curator import Curator
from src.roles.planner import Planner
from src.roles.synthesizer import Synthesizer
from src.roles.archivist import Archivist


def run_once(input_text: str):
    payload = {"input": input_text}
    for role_cls in [Watcher, Curator, Planner, Synthesizer, Archivist]:
        role = role_cls()
        payload = role.run(payload)


if __name__ == "__main__":
    import sys

    input_text = sys.argv[1] if len(sys.argv) > 1 else "hello"
    run_once(input_text)
