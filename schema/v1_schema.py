from typing import Any, Dict
from datetime import datetime

ROLE_SET = {"Watcher", "Curator", "Planner", "Synthesizer", "Archivist"}


def is_iso8601(s: str) -> bool:
    """Check if a string is valid ISO8601 format."""
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def validate_payload(payload: Dict[str, Any], stage: str) -> None:
    """Validate payload against schema requirements.

    Args:
        payload: The data dictionary to validate
        stage: Description of validation stage (e.g., "in:Watcher", "out:Curator")

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(payload, dict):
        raise ValueError(f"[{stage}] payload must be dict")

    # Initial input case (for Watcher's first input)
    if "input" in payload and isinstance(payload["input"], str):
        # This is valid initial input
        return

    # Standard output schema validation
    required = ["role", "output"]
    for k in required:
        if k not in payload:
            raise ValueError(f"[{stage}] missing key: {k}")

    if payload["role"] not in ROLE_SET:
        raise ValueError(f"[{stage}] invalid role: {payload['role']}")

    if not isinstance(payload["output"], str):
        raise ValueError(f"[{stage}] output must be str")

    # Optional keys validation
    if "ts" in payload:
        if not isinstance(payload["ts"], str) or not is_iso8601(payload["ts"]):
            raise ValueError(f"[{stage}] ts must be ISO8601 str")

    if "refs" in payload:
        if not isinstance(payload["refs"], list):
            raise ValueError(f"[{stage}] refs must be list")
