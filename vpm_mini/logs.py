# vpm_mini/logs.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def append_turn(
    ts: float,
    role: str,
    text: str,
    session_id: str,
    refs: list[str] | None = None,
) -> Path:
    """Append a single turn to today's log file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = log_dir / f"{date_str}.jsonl"

    turn = {
        "ts": ts,
        "session_id": session_id,
        "role": role,
        "text": text,
        "refs": refs or [],
        "meta": {"lang": "ja"},
    }

    with open(log_path, "a", encoding="utf-8") as f:
        json.dump(turn, f, ensure_ascii=False)
        f.write("\n")

    return log_path


def append_chatlog(turns: list[dict], session_id: str) -> Path:
    """Append multiple turns to today's log file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = log_dir / f"{date_str}.jsonl"

    with open(log_path, "a", encoding="utf-8") as f:
        for turn in turns:
            # Ensure required fields
            event = {
                "ts": turn.get("ts", datetime.now().timestamp()),
                "session_id": session_id,
                "role": turn.get("role", "user"),
                "text": turn.get("text", ""),
                "refs": turn.get("refs", []),
                "meta": turn.get("meta", {"lang": "ja"}),
            }
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")

    return log_path


def read_logs(log_path: str | Path) -> list[dict]:
    """Read all events from a JSONL log file."""
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def extract_text_from_logs(log_path: str | Path) -> str:
    """Extract and concatenate all text from a log file."""
    events = read_logs(log_path)
    texts = []
    for event in events:
        if event.get("text"):
            texts.append(event["text"])
    return "\n\n".join(texts)
