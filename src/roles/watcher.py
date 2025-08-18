from datetime import datetime, timezone
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from schema.v1_schema import validate_payload
from src.egspace.store import (
    new_vec_id,
    append_event,
    register_index,
    get_today_raw_ref,
)


class Watcher:
    def run(self, payload: dict) -> dict:
        validate_payload(payload, "in:Watcher")
        print("[Watcher] received:", payload)

        # Create base result
        result = {
            "role": "Watcher",
            "output": "dummy output from Watcher",
            "ts": datetime.now(timezone.utc).isoformat(),
            "refs": [],
        }

        # EG-Space integration
        vec_id = new_vec_id("session")
        event = {
            "vec_id": vec_id,
            "role": "Watcher",
            "payload": payload,
            "result": result,
            "ts": result["ts"],
        }
        append_event(event)

        # Register in index with placeholder raw_ref
        raw_ref = get_today_raw_ref()
        register_index(vec_id, raw_ref)

        # Add vec_id to result refs
        result["refs"].append(vec_id)
        print(f"wrote to egspace: {vec_id}")

        validate_payload(result, "out:Watcher")
        print("[Watcher] in/out: OK")
        return result
