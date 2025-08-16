# tests/test_egspace.py
import json
from pathlib import Path

from vpm_mini.egspace import ingest_jsonl, get_stats


def test_ingest_jsonl(tmp_path, monkeypatch):
    """Test ingesting JSONL and assigning stable IDs."""
    monkeypatch.chdir(tmp_path)

    # Create test JSONL
    test_jsonl = tmp_path / "test.jsonl"
    events = [
        {"ts": 1723854000.0, "role": "user", "text": "test1"},
        {"ts": 1723854060.0, "role": "assistant", "text": "test2"},
    ]

    with open(test_jsonl, "w", encoding="utf-8") as f:
        for event in events:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")

    # Ingest
    processed = ingest_jsonl(str(test_jsonl))

    # Verify
    assert len(processed) == 2
    assert processed[0]["id"].startswith("E:")
    assert "#1" in processed[0]["id"]
    assert "#2" in processed[1]["id"]

    # Check events file
    events_file = Path("egspace/events.jsonl")
    assert events_file.exists()

    # Check index file
    index_file = Path("egspace/index.json")
    assert index_file.exists()

    with open(index_file, "r", encoding="utf-8") as f:
        index = json.load(f)

    # Should have one date entry
    assert len(index) == 1
    date_key = list(index.keys())[0]
    assert index[date_key]["count"] == 2


def test_get_stats(tmp_path, monkeypatch):
    """Test getting EG-Space statistics."""
    monkeypatch.chdir(tmp_path)

    # Initially no stats
    stats = get_stats()
    assert stats["total_events"] == 0
    assert stats["latest_id"] is None

    # Create index
    egspace_dir = Path("egspace")
    egspace_dir.mkdir(exist_ok=True)

    index_data = {
        "2025-08-16": {
            "date": "2025-08-16",
            "count": 5,
            "updated_at": "2025-08-16T12:00:00Z",
        },
        "2025-08-17": {
            "date": "2025-08-17",
            "count": 3,
            "updated_at": "2025-08-17T14:00:00Z",
        },
    }

    with open(egspace_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index_data, f)

    # Get stats
    stats = get_stats()
    assert stats["total_events"] == 8
    assert stats["latest_id"] == "E:2025-08-17#3"
