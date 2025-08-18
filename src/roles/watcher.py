from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload


class Watcher:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Watcher")
        print("[Watcher] received:", payload)

        result = {
            "role": "Watcher",
            "output": "dummy output from Watcher",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }
        validate_payload(result, "out:Watcher")
        print("[Watcher] in/out: OK")
        return result
