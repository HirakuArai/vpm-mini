import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from core.state_drafter import draft_state

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / "STATE"


def _make_decision(dir_path: Path, name: str, **fields):
    dir_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": fields.get("id", name),
        "decision": fields.get("decision", "採用"),
        "rationale": fields.get("rationale", "理由"),
        "links": fields.get("links", ["https://example.com"]),
    }
    (dir_path / name).write_text(
        "\n".join(
            [
                f"id: {payload['id']}",
                f"decision: {payload['decision']}",
                f"rationale: {payload['rationale']}",
                "links:",
            ]
            + [f"  - {link}" for link in payload["links"]]
        )
        + "\n",
        encoding="utf-8",
    )


def test_draft_state_rule_mode(tmp_path):
    decisions_dir = tmp_path / "decisions"
    _make_decision(
        decisions_dir,
        "D-20251018-test.yml",
        id="D-20251018",
        decision="Proceed",
        rationale="Coverage ok",
    )

    result = draft_state(decisions_dir=decisions_dir, use_ai=False, max_items=5)

    assert result["body"].startswith("# === STATE Update")
    assert "D-20251018" in result["body"]
    assert any("STATE/current_state.md" in src for src in result["sources"])


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY is not configured",
)
def test_draft_state_ai_mode(tmp_path):
    decisions_dir = tmp_path / "decisions"
    _make_decision(
        decisions_dir,
        "D-20251019-test.yml",
        id="D-20251019",
        decision="Adopt",
        rationale="Confidence high",
    )

    result = draft_state(decisions_dir=decisions_dir, use_ai=True, max_items=3)
    assert "body" in result and isinstance(result["body"], str)
    assert isinstance(result.get("sources"), list)


def test_cli_state_update_generates_file(tmp_path):
    decisions_dir = tmp_path / "decisions"
    _make_decision(
        decisions_dir,
        "D-20251020-test.yml",
        id="D-20251020",
        decision="Ship",
        rationale="Green",
    )

    before = set(STATE_DIR.glob("update_*.md"))
    try:
        subprocess.run(
            [
                sys.executable,
                "cli.py",
                "state-update",
                "--decisions-dir",
                str(decisions_dir),
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        after = set(STATE_DIR.glob("update_*.md"))
        new_files = after - before
        assert new_files, "STATE update file was not created"
    finally:
        for path in set(STATE_DIR.glob("update_*.md")) - before:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
