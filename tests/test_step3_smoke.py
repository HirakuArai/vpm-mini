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


def test_cli_plan_generates_json(tmp_path):
    original_inventory = INVENTORY_PATH.read_text(encoding="utf-8")
    try:
        rows = [
            [
                "ASSET-001",
                "analytics",
                "KPI Dashboard",
                "owner_a",
                "H",
                "pending",
                (date.today() + timedelta(days=14)).isoformat(),
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
        _write_inventory(rows)
        decision_file = DECISIONS_DIR / "D-test-plan.yml"
        decision_file.write_text(
            "id: D-test\ndecision: 'Move KPI dashboard'\nrationale: 'Align with goals'\nlinks:\n  - PR #101\n",
            encoding="utf-8",
        )
        out_path = tmp_path / "plan.json"
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
        (DECISIONS_DIR / "D-test-plan.yml").unlink(missing_ok=True)


def test_cli_plan_json_stdout(tmp_path):
    original_inventory = INVENTORY_PATH.read_text(encoding="utf-8")
    try:
        rows = [
            [
                "ASSET-001",
                "analytics",
                "KPI Dashboard",
                "owner_a",
                "H",
                "pending",
                (date.today() + timedelta(days=7)).isoformat(),
                "S",
                "HIGH",
                "rehost",
                "PR #102",
            ]
        ]
        _write_inventory(rows)
        decision_file = DECISIONS_DIR / "D-test-plan-json.yml"
        decision_file.write_text(
            "id: D-test-json\ndecision: 'Rehost KPI dashboard'\nrationale: 'Reduce toil'\nlinks:\n  - PR #102\n",
            encoding="utf-8",
        )
        out_path = tmp_path / "plan_stdout.json"
        result = subprocess.run(
            [
                sys.executable,
                "cli.py",
                "plan",
                "--limit",
                "1",
                "--out",
                str(out_path),
                "--json-stdout",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        stdout_json = result.stdout.strip()
        assert stdout_json, "stdout should contain JSON"
        data_stdout = json.loads(stdout_json)
        data_file = json.loads(out_path.read_text(encoding="utf-8"))
        assert data_stdout == data_file
        assert data_stdout.get("next_actions"), "next_actions should not be empty"
    finally:
        INVENTORY_PATH.write_text(original_inventory, encoding="utf-8")
        (DECISIONS_DIR / "D-test-plan-json.yml").unlink(missing_ok=True)


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
