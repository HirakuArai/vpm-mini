import sys
import os
import json

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.egspace.store import (
    ensure_dirs,
    new_vec_id,
    append_event,
    register_index,
    get_today_raw_ref,
    EG_DIR,
    EV_FILE,
    IDX_FILE,
)
from src.roles.watcher import Watcher
from src.roles.curator import Curator


def test_ensure_dirs(tmp_path, monkeypatch):
    """Test that ensure_dirs creates necessary directories and files."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Ensure directories don't exist initially
    assert not EG_DIR.exists()

    # Run ensure_dirs
    ensure_dirs()

    # Check that directories and files are created
    assert EG_DIR.exists()
    assert EG_DIR.is_dir()
    assert EV_FILE.exists()
    assert IDX_FILE.exists()

    # Check initial content
    assert EV_FILE.read_text() == ""
    assert IDX_FILE.read_text() == "{}"


def test_new_vec_id_uniqueness():
    """Test that new_vec_id generates unique IDs."""
    ids = set()

    # Generate multiple IDs and ensure they're unique
    for _ in range(10):
        vec_id = new_vec_id("test")
        assert vec_id not in ids, f"Duplicate ID generated: {vec_id}"
        ids.add(vec_id)

        # Verify format
        assert vec_id.startswith("test_")
        assert "_" in vec_id
        parts = vec_id.split("_")
        assert len(parts) >= 5  # test_YYYYMMDD_HHMMSS_mmm_nnnn


def test_append_event_and_register_index(tmp_path, monkeypatch):
    """Test appending events and registering in index."""
    monkeypatch.chdir(tmp_path)

    # Create test event
    test_event = {
        "vec_id": "test_123_456",
        "role": "TestRole",
        "payload": {"input": "test"},
        "result": {"output": "test output"},
        "ts": "2025-08-18T12:00:00Z",
    }

    # Append event
    vec_id = append_event(test_event)
    assert vec_id == "test_123_456"

    # Check that event was written to file
    assert EV_FILE.exists()
    with EV_FILE.open("r") as f:
        lines = f.readlines()

    assert len(lines) == 1
    stored_event = json.loads(lines[0])
    assert stored_event == test_event

    # Register in index
    raw_ref = "logs/2025-08-18/test.jsonl#L1"
    register_index(vec_id, raw_ref)

    # Check index was updated
    assert IDX_FILE.exists()
    with IDX_FILE.open("r") as f:
        index = json.load(f)

    assert vec_id in index
    assert index[vec_id] == raw_ref


def test_get_today_raw_ref():
    """Test that get_today_raw_ref returns proper format."""
    raw_ref = get_today_raw_ref()

    assert raw_ref.startswith("logs/")
    assert raw_ref.endswith("/session.jsonl#latest")
    assert len(raw_ref.split("/")[1]) == 10  # YYYY-MM-DD format


def test_watcher_egspace_integration(tmp_path, monkeypatch):
    """Test that Watcher integrates with EG-Space correctly."""
    monkeypatch.chdir(tmp_path)

    watcher = Watcher()
    payload = {"input": "test input"}

    result = watcher.run(payload)

    # Check that result has vec_id in refs
    assert "refs" in result
    assert len(result["refs"]) == 1
    vec_id = result["refs"][0]
    assert vec_id.startswith("session_")

    # Check that event was written to events.jsonl
    assert EV_FILE.exists()
    with EV_FILE.open("r") as f:
        lines = f.readlines()

    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["vec_id"] == vec_id
    assert event["role"] == "Watcher"
    assert event["payload"] == payload

    # Check that index was updated
    with IDX_FILE.open("r") as f:
        index = json.load(f)

    assert vec_id in index
    assert "logs/" in index[vec_id]


def test_curator_egspace_integration(tmp_path, monkeypatch):
    """Test that Curator integrates with EG-Space correctly."""
    monkeypatch.chdir(tmp_path)

    curator = Curator()
    payload = {
        "role": "Watcher",
        "output": "previous output",
        "ts": "2025-08-18T12:00:00Z",
        "refs": ["session_prev_0001"],
    }

    result = curator.run(payload)

    # Check that result has vec_id in refs
    assert "refs" in result
    assert len(result["refs"]) == 1
    vec_id = result["refs"][0]
    assert vec_id.startswith("session_")

    # Check that event was written to events.jsonl
    assert EV_FILE.exists()
    with EV_FILE.open("r") as f:
        lines = f.readlines()

    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["vec_id"] == vec_id
    assert event["role"] == "Curator"
    assert event["payload"] == payload


def test_multiple_roles_egspace_integration(tmp_path, monkeypatch):
    """Test that multiple roles write to EG-Space correctly."""
    monkeypatch.chdir(tmp_path)

    # Run Watcher then Curator
    watcher = Watcher()
    payload = {"input": "test input"}
    watcher_result = watcher.run(payload)

    curator = Curator()
    curator.run(watcher_result)

    # Check that we have 2 events in events.jsonl
    with EV_FILE.open("r") as f:
        lines = f.readlines()

    assert len(lines) == 2

    # Check that both events have unique vec_ids
    event1 = json.loads(lines[0])
    event2 = json.loads(lines[1])

    assert event1["vec_id"] != event2["vec_id"]
    assert event1["role"] == "Watcher"
    assert event2["role"] == "Curator"

    # Check that index has both entries
    with IDX_FILE.open("r") as f:
        index = json.load(f)

    assert len(index) == 2
    assert event1["vec_id"] in index
    assert event2["vec_id"] in index
