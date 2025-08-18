import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timezone

from schema.v1_schema import validate_payload, is_iso8601
from src.roles.watcher import Watcher
from src.roles.curator import Curator
from src.roles.planner import Planner
from src.roles.synthesizer import Synthesizer
from src.roles.archivist import Archivist


def test_is_iso8601():
    """Test ISO8601 validation function."""
    # Valid ISO8601 strings
    assert is_iso8601("2025-08-17T12:00:00+00:00")
    assert is_iso8601("2025-08-17T12:00:00Z")
    assert is_iso8601(datetime.now(timezone.utc).isoformat())

    # Invalid strings
    assert not is_iso8601("not a date")
    assert not is_iso8601("2025-13-01T00:00:00Z")  # Invalid month
    assert not is_iso8601("")


def test_validate_payload_initial_input():
    """Test validation accepts initial input format."""
    # Valid initial input for Watcher
    payload = {"input": "hello"}
    validate_payload(payload, "in:Watcher")  # Should not raise


def test_validate_payload_standard_output():
    """Test validation of standard output format."""
    # Valid standard output
    payload = {
        "role": "Watcher",
        "output": "some output",
        "ts": datetime.now(timezone.utc).isoformat(),
        "refs": [],
    }
    validate_payload(payload, "out:Watcher")  # Should not raise


def test_validate_payload_missing_required():
    """Test validation fails when required keys are missing."""
    # Missing 'output' key
    payload = {"role": "Watcher"}
    with pytest.raises(ValueError, match="missing key: output"):
        validate_payload(payload, "out:Watcher")

    # Missing 'role' key
    payload = {"output": "test"}
    with pytest.raises(ValueError, match="missing key: role"):
        validate_payload(payload, "out:Watcher")


def test_validate_payload_invalid_role():
    """Test validation fails for invalid role names."""
    payload = {"role": "InvalidRole", "output": "test"}
    with pytest.raises(ValueError, match="invalid role"):
        validate_payload(payload, "out:InvalidRole")


def test_validate_payload_wrong_types():
    """Test validation fails for wrong data types."""
    # Not a dict
    with pytest.raises(ValueError, match="payload must be dict"):
        validate_payload("not a dict", "test")

    # Output not a string
    payload = {"role": "Watcher", "output": 123}
    with pytest.raises(ValueError, match="output must be str"):
        validate_payload(payload, "out:Watcher")

    # refs not a list
    payload = {"role": "Watcher", "output": "test", "refs": "not a list"}
    with pytest.raises(ValueError, match="refs must be list"):
        validate_payload(payload, "out:Watcher")


def test_full_pipeline():
    """Test the full 5-role pipeline with validation."""
    # Start with initial input
    payload = {"input": "hello"}

    # Run through all roles
    for role_cls in [Watcher, Curator, Planner, Synthesizer, Archivist]:
        role = role_cls()
        payload = role.run(payload)

        # Verify output format
        assert "role" in payload
        assert "output" in payload
        assert "ts" in payload
        assert "refs" in payload
        assert isinstance(payload["output"], str)
        assert isinstance(payload["refs"], list)
        assert is_iso8601(payload["ts"])

    # Final output should be from Archivist
    assert payload["role"] == "Archivist"


def test_invalid_input_to_role():
    """Test that roles reject invalid input."""
    # Create a Curator (expects previous role output, not initial input)
    curator = Curator()

    # Try to pass invalid payload (missing required keys)
    invalid_payload = {"invalid": "data"}

    with pytest.raises(ValueError):
        curator.run(invalid_payload)
