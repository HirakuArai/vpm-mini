from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload


class Planner:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Planner")
        print("[Planner] received:", payload)

        result = {
            "role": "Planner",
            "output": "dummy output from Planner",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }
        validate_payload(result, "out:Planner")
        print("[Planner] in/out: OK")
        return result
