import textwrap

from guard.validate_json import validate_answer, validate_plan, validate_state_md


def test_validate_answer_ok(tmp_path):
    payload = {
        "answer": "OK",
        "sources": ["inventory/inventory.csv", "STATE/current_state.md"],
        "confidence": 0.8,
        "unknown_fields": [],
    }
    ok, errors = validate_answer(payload)
    assert ok, errors


def test_validate_plan_ok(tmp_path):
    payload = {
        "next_actions": [
            {
                "id": "A1",
                "title": "Action",
                "priority": 1,
                "DoD": ["Check"],
                "owner": "owner",
                "due": "",
                "links": [],
                "sources": ["inventory/inventory.csv"],
            }
        ]
    }
    ok, errors = validate_plan(payload)
    assert ok, errors


def test_validate_state_ok():
    md = textwrap.dedent(
        """
        # === STATE Update (Decisions sync) ===

        ## Sources
        - inventory/inventory.csv
        """
    ).strip()
    ok, errors = validate_state_md(md)
    assert ok, errors


def test_validate_answer_missing_sources():
    payload = {
        "answer": "test",
        "sources": [],
        "confidence": 0.1,
        "unknown_fields": [],
    }
    ok, errors = validate_answer(payload)
    assert not ok
    assert any("sources" in err for err in errors)


def test_validate_plan_missing_dod():
    payload = {
        "next_actions": [
            {
                "id": "A1",
                "title": "Action",
                "priority": 1,
                "DoD": [],
                "owner": "owner",
                "links": [],
                "sources": ["inventory/inventory.csv"],
            }
        ]
    }
    ok, errors = validate_plan(payload)
    assert not ok
    assert any("DoD" in err for err in errors)


def test_validate_state_missing_title():
    md = "## Sources\n - inventory/inventory.csv"
    ok, errors = validate_state_md(md)
    assert not ok
    assert any("title" in err for err in errors)
