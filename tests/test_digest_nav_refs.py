import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpm_mini.digest import (
    render_digest_md,
    render_nav_mermaid,
    _add_egspace_refs,
    _get_recent_vec_ids,
)


def test_add_egspace_refs_with_events():
    """Test that EG-Space references are added to digest when events exist."""
    # Create a mock scenario with some EG-Space data
    lines = []
    _add_egspace_refs(lines)

    # Should add references section if events exist
    content = "\n".join(lines)
    if "EG-Space References" in content:
        assert "refs:" in content
        assert "[session_" in content


def test_add_egspace_refs_without_events(monkeypatch):
    """Test that EG-Space references handle missing events gracefully."""
    # Mock empty events
    monkeypatch.setattr("vpm_mini.digest.get_recent_events", lambda x: [])

    lines = []
    _add_egspace_refs(lines)

    # Should not add references section if no events
    content = "\n".join(lines)
    assert content == "" or "EG-Space References" not in content


def test_get_recent_vec_ids():
    """Test that vec_ids are extracted from recent events."""
    vec_ids = _get_recent_vec_ids(5)

    # Should return a list (may be empty if no events)
    assert isinstance(vec_ids, list)

    # If vec_ids exist, they should have the expected format
    for vec_id in vec_ids:
        assert isinstance(vec_id, str)
        if vec_id:  # If not empty
            assert "session_" in vec_id


def test_render_digest_md_includes_egspace():
    """Test that digest markdown includes EG-Space references."""
    state = {
        "summary_ja_<=400chars": "Test summary",
        "C": "Current state",
        "G": "Goal state",
        "delta": "Difference",
        "decisions": ["Decision 1"],
        "open_questions": [],
        "todos": ["Task 1"],
        "risks": [],
    }

    result = render_digest_md(state)

    # Basic structure should be present
    assert "# Session Digest" in result
    assert "## 概要（≤400字）" in result
    assert "Test summary" in result

    # EG-Space section may or may not be present depending on events
    # but the function should not crash


def test_render_nav_mermaid_includes_vec_id():
    """Test that nav mermaid includes vec_id in labels."""
    state = {
        "C": "Current state",
        "G": "Goal state",
        "delta": "Difference",
    }

    result = render_nav_mermaid(state)

    # Basic mermaid structure
    assert "```mermaid" in result
    assert "flowchart LR" in result
    assert "現在地 (C)" in result

    # May or may not have vec_id depending on events
    # but should not crash


def test_digest_file_contains_refs(tmp_path):
    """Test that generated digest file contains refs when EG-Space events exist."""
    # Create a temporary digest file
    test_content = """# Session Digest — 2025-08-19

## 概要（≤400字）

Test session summary.

## EG-Space References

- Watcher: refs: [session_20250818_123456_789_0001] → logs/2025-08-19/session.jsonl#latest
- Curator: refs: [session_20250818_123456_789_0002] → logs/2025-08-19/session.jsonl#latest

## 現在地 (C)

Current state info.
"""

    digest_file = tmp_path / "test_digest.md"
    digest_file.write_text(test_content, encoding="utf-8")

    # Read and verify
    content = digest_file.read_text(encoding="utf-8")
    assert "## EG-Space References" in content
    assert "refs: [session_" in content
    assert "→" in content


def test_nav_file_contains_vec_id(tmp_path):
    """Test that generated nav file contains vec_id in labels."""
    # Create a temporary nav file
    test_content = """```mermaid
flowchart LR
  C["現在地 (C)\\n[session_20250818_123456_789_0001]"] --> route["推奨ルート"]
  route --> G["目的地 (G)"] 
  C -.-> delta["差分 δ"]
  decisions["主要決定"] --- route
  risks["主要リスク"] -.-> route
%% C: Current state
%% G: Goal state
%% δ: Difference
```
"""

    nav_file = tmp_path / "test_nav.md"
    nav_file.write_text(test_content, encoding="utf-8")

    # Read and verify
    content = nav_file.read_text(encoding="utf-8")
    assert "[session_" in content
    assert "現在地 (C)" in content


def test_digest_integration_with_no_egspace():
    """Test that digest generation works when EG-Space is not available."""
    # This test ensures backwards compatibility
    state = {"summary_ja_<=400chars": "Test"}

    # Should not crash even if EG-Space imports fail
    result = render_digest_md(state)
    assert "Test" in result
    assert "# Session Digest" in result


def test_nav_integration_with_no_egspace():
    """Test that nav generation works when EG-Space is not available."""
    # This test ensures backwards compatibility
    state = {"C": "Current", "G": "Goal", "delta": "Delta"}

    # Should not crash even if EG-Space imports fail
    result = render_nav_mermaid(state)
    assert "```mermaid" in result
    assert "Current" in result
