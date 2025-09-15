from fastapi.testclient import TestClient
from pathlib import Path

from app.__init__ import app

client = TestClient(app)


def test_create_task_and_evidence(tmp_path, monkeypatch):
    # Evidence出力先を一時ディレクトリに迂回
    from app.core import evidence as evid

    monkeypatch.setattr(evid, "EVID_DIR", Path(tmp_path / "trial_tasks"))

    payload = {
        "title": "Trial input",
        "description": "first",
        "priority": "mid",
        "tags": ["trial", "ui"],
    }
    r = client.post("/api/v1/tasks", json=payload)
    assert (
        r.status_code == 200
    )  # FastAPI returns 200 by default for successful operations
    body = r.json()
    assert "trace_id" in body and body["trace_id"].startswith("tr_")

    # Evidence 作成確認
    files = list((tmp_path / "trial_tasks").glob("*.md"))
    assert files, "md evidence not created"
    jls = list((tmp_path / "trial_tasks").glob("*.jsonl"))
    assert jls, "jsonl evidence not created"
