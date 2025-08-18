# vpm_mini/egspace.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def ingest_jsonl(jsonl_path: str) -> list[dict]:
    """Ingest events from JSONL log file and assign stable IDs."""
    egspace_dir = Path("egspace")
    egspace_dir.mkdir(exist_ok=True)

    events_path = egspace_dir / "events.jsonl"
    index_path = egspace_dir / "index.json"

    # Load current index
    index = {}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

    # Read input events
    input_events = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                input_events.append(json.loads(line))

    # Process events by date
    processed = []
    for event in input_events:
        # Extract date from timestamp
        ts = event.get("ts", datetime.now(timezone.utc).timestamp())
        dt = datetime.fromtimestamp(ts, timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")

        # Get or initialize counter for this date
        if date_str not in index:
            index[date_str] = {"date": date_str, "count": 0, "updated_at": ""}

        # Assign stable ID
        index[date_str]["count"] += 1
        event_id = f"E:{date_str}#{index[date_str]['count']}"

        # Add ID to event
        event_with_id = {"id": event_id, **event}
        processed.append(event_with_id)

        # Append to events file
        with open(events_path, "a", encoding="utf-8") as f:
            json.dump(event_with_id, f, ensure_ascii=False)
            f.write("\n")

    # Update index timestamps
    for date_str in index:
        if index[date_str]["count"] > 0:
            index[date_str]["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save index
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return processed


def get_stats() -> dict:
    """Get EG-Space statistics for digest snapshot."""
    index_path = Path("egspace/index.json")
    if not index_path.exists():
        return {"total_events": 0, "latest_id": None}

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    total = sum(entry.get("count", 0) for entry in index.values())

    # Find latest ID
    latest_id = None
    latest_date = None
    for date_str, entry in index.items():
        if entry.get("count", 0) > 0:
            if latest_date is None or date_str > latest_date:
                latest_date = date_str
                latest_id = f"E:{date_str}#{entry['count']}"

    return {
        "total_events": total,
        "latest_id": latest_id,
    }
