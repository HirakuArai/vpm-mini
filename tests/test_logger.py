import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from src.core.logger import append_log, _today_filename
import json


def test_append_log_creates_file(tmp_path, monkeypatch):
    # isolate log dir
    monkeypatch.setattr("src.core.logger.LOG_DIR", tmp_path)
    append_log({"role": "user", "content": "hello"})
    file_path = _today_filename()
    assert file_path.exists()
    with file_path.open(encoding="utf-8") as f:
        rec = json.loads(f.readline())
    assert rec["role"] == "user"
    assert rec["timestamp"].endswith("Z")
