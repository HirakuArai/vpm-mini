"""Central JSONL logger for Chat-UI messages (UTC)."""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("objectives") / "vpm-mini" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _today_filename() -> Path:
    """Return today's log file path (UTC date)."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return LOG_DIR / f"{date_str}.jsonl"


def append_log(entry: dict) -> None:
    """Append one NDJSON record, adding timestamp if missing."""
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    with _today_filename().open("a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
        f.write("\n")


# convenience for unit test
__all__ = ["append_log", "_today_filename"]
