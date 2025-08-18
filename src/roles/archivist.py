from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload


class Archivist:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Archivist")
        print("[Archivist] received:", payload)

        result = {
            "role": "Archivist",
            "output": "dummy output from Archivist",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }
        validate_payload(result, "out:Archivist")
        print("[Archivist] in/out: OK")
        return result
