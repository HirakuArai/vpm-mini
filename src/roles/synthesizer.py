from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload


class Synthesizer:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Synthesizer")
        print("[Synthesizer] received:", payload)

        result = {
            "role": "Synthesizer",
            "output": "dummy output from Synthesizer",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }
        validate_payload(result, "out:Synthesizer")
        print("[Synthesizer] in/out: OK")
        return result
