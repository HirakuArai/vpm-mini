import json
import time
from datetime import datetime
from pathlib import Path

EG_DIR = Path("egspace")
EV_FILE = EG_DIR / "events.jsonl"
IDX_FILE = EG_DIR / "index.json"


def ensure_dirs():
    """Ensure egspace directory and files exist."""
    EG_DIR.mkdir(exist_ok=True)
    if not EV_FILE.exists():
        EV_FILE.write_text("")
    if not IDX_FILE.exists():
        IDX_FILE.write_text("{}")


def new_vec_id(prefix="session") -> str:
    """Generate new unique vector ID."""
    import random

    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    # Add milliseconds and random suffix to ensure uniqueness
    ms = int(time.time() * 1000) % 1000
    suffix = random.randint(1000, 9999)

    vid = f"{prefix}_{ts}_{ms:03d}_{suffix}"
    return vid


def _load_index() -> dict:
    """Load index.json as dictionary."""
    ensure_dirs()
    try:
        content = IDX_FILE.read_text() or "{}"
        return json.loads(content)
    except Exception:
        return {}


def _save_index(d: dict):
    """Save dictionary to index.json."""
    IDX_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def append_event(event: dict) -> str:
    """Append event to events.jsonl and return vec_id."""
    ensure_dirs()

    # Ensure vec_id exists
    if "vec_id" not in event:
        event["vec_id"] = new_vec_id()

    vec_id = event["vec_id"]

    # Append to events file
    with EV_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return vec_id


def register_index(vec_id: str, raw_ref: str) -> None:
    """Register vec_id -> raw_ref mapping in index."""
    index = _load_index()
    index[vec_id] = raw_ref
    _save_index(index)


def get_today_raw_ref() -> str:
    """Get a placeholder raw_ref for today's log."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"logs/{today}/session.jsonl#latest"
