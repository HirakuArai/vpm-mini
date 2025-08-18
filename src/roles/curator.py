from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload


class Curator:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Curator")
        print("[Curator] received:", payload)

        result = {
            "role": "Curator",
            "output": "dummy output from Curator",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }
        validate_payload(result, "out:Curator")
        print("[Curator] in/out: OK")
        return result
