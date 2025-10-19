import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "inventory" / "inventory.csv"
DECISIONS_DIR = REPO_ROOT / "reports" / "decisions"


def _write_inventory(rows):
    header = [
        "asset_id",
        "kind",
        "name",
        "owner",
        "criticality",
        "status",
        "due_date",
        "est_effort",
        "risk",
        "target_option",
        "links",
    ]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(row))
    INVENTORY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_decision(path: Path, *, decision: str, rationale: str, links=None):
    links = links or []
    payload = {
        "id": path.stem,
        "decision": decision,
        "rationale": rationale,
        "links": links,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cli_plan_generates_json(tmp_path):
    days_ahead = (date.today() + timedelta(days=14)).isoformat()
    rows = [
        [
            "ASSET-001",
            "analytics",
            "KPI Dashboard",
            "owner_a",
            "H",
            "pending",
            days_ahead,
            "S",
            "HIGH",
            "rehost",
            "PR #101",
        ],
        [
            "ASSET-002",
            "etl",
            "ETL Job",
            "owner_b",
            "M",
            "pending",
            "",
            "M",
            "MED",
            "refactor",
            "",
        ],
    ]
    original_inventory = INVENTORY_PATH.read_text(encoding="utf-8")
    _write_inventory(rows)

    decision_file = DECISIONS_DIR / "D-test-plan.yml"
    decision_file.write_text(
        "id: D-test\ndecision: 'Move KPI dashboard to managed service'\n"
        "rationale: 'Align with Phase 2 goal'\nlinks:\n  - PR #101\n",
        encoding="utf-8",
    )

    out_path = tmp_path / "plan.json"
    try:
        subprocess.run(
            [
                sys.executable,
                "cli.py",
                "plan",
                "--limit",
                "2",
                "--out",
                str(out_path),
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["next_actions"], "next_actions should not be empty"
        first = data["next_actions"][0]
        for key in ("id", "title", "priority", "DoD", "owner", "sources"):
            assert key in first
    finally:
        INVENTORY_PATH.write_text(original_inventory, encoding="utf-8")
        decision_file.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY is not configured",
)
def test_cli_plan_ai_mode_structure(tmp_path):
    out_path = tmp_path / "plan_ai.json"
    subprocess.run(
        [
            sys.executable,
            "cli.py",
            "plan",
            "--ai",
            "--limit",
            "1",
            "--out",
            str(out_path),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    data = json.loads(out_path.read_text(encoding="utf-8"))
    for key in ("next_actions", "short_goal"):
        assert key in data
    if data["next_actions"]:
        action = data["next_actions"][0]
        for key in ("id", "title", "priority", "DoD", "owner", "sources"):
            assert key in action
