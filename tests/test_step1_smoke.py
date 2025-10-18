import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from core.grounded_answer import grounded_answer


REQUIRED_KEYS = {"answer", "sources", "confidence", "unknown_fields"}


def test_grounded_answer_rule_mode_structure():
    result = grounded_answer("今のPhaseは？", use_ai=False)
    assert REQUIRED_KEYS.issubset(result)
    assert isinstance(result["sources"], list)
    assert isinstance(result["unknown_fields"], list)
    assert 0.0 <= float(result["confidence"]) <= 1.0


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY is not configured",
)
def test_grounded_answer_ai_mode_structure():
    result = grounded_answer("進捗は？", use_ai=True)
    assert REQUIRED_KEYS.issubset(result)
    assert isinstance(result["sources"], list)
    assert isinstance(result["unknown_fields"], list)
    assert 0.0 <= float(result["confidence"]) <= 1.0
