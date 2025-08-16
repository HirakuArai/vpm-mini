# tests/test_logs.py
import json
from datetime import datetime

from vpm_mini.logs import append_turn, append_chatlog, read_logs


def test_append_turn(tmp_path, monkeypatch):
    """Test appending a single turn to log file."""
    monkeypatch.chdir(tmp_path)

    ts = datetime.now().timestamp()
    log_path = append_turn(
        ts=ts,
        role="user",
        text="テストメッセージ",
        session_id="S:2025-08-17#1",
        refs=["file:test.md"],
    )

    assert log_path.exists()

    # Read and verify
    with open(log_path, "r", encoding="utf-8") as f:
        line = f.readline()
        event = json.loads(line)

    assert event["ts"] == ts
    assert event["role"] == "user"
    assert event["text"] == "テストメッセージ"
    assert event["session_id"] == "S:2025-08-17#1"
    assert event["refs"] == ["file:test.md"]
    assert event["meta"]["lang"] == "ja"


def test_append_chatlog(tmp_path, monkeypatch):
    """Test appending multiple turns."""
    monkeypatch.chdir(tmp_path)

    turns = [
        {"role": "user", "text": "質問1"},
        {"role": "assistant", "text": "回答1"},
    ]

    log_path = append_chatlog(turns, "S:2025-08-17#2")

    events = read_logs(log_path)
    assert len(events) == 2
    assert events[0]["text"] == "質問1"
    assert events[1]["text"] == "回答1"
    assert all(e["session_id"] == "S:2025-08-17#2" for e in events)
