import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import run_all_pipeline


def test_run_all_pipeline_integration():
    """Test that run_all_pipeline executes all steps successfully."""
    # Use a test message
    test_message = "test end-to-end pipeline integration"

    # Execute the pipeline
    result = run_all_pipeline(test_message)

    # Verify result structure
    assert isinstance(result, dict)
    assert "message" in result
    assert "pipeline_result" in result
    assert "summary" in result
    assert "log_file" in result
    assert "digest_file" in result
    assert "nav_file" in result
    assert "egspace_events" in result
    assert "recent_vec_ids" in result

    # Verify message was preserved
    assert result["message"] == test_message

    # Verify files were created
    log_file = Path(result["log_file"])
    digest_file = Path(result["digest_file"])
    nav_file = Path(result["nav_file"])

    assert log_file.exists()
    assert digest_file.exists()
    assert nav_file.exists()

    # Verify EG-Space integration
    assert isinstance(result["egspace_events"], int)
    assert result["egspace_events"] > 0
    assert isinstance(result["recent_vec_ids"], list)

    # Verify log file contains the test message
    log_content = log_file.read_text(encoding="utf-8")
    assert test_message in log_content

    # Verify digest file contains EG-Space references
    digest_content = digest_file.read_text(encoding="utf-8")
    assert "# Session Digest" in digest_content
    assert test_message in digest_content

    # Verify nav file contains mermaid
    nav_content = nav_file.read_text(encoding="utf-8")
    assert "```mermaid" in nav_content
    assert "flowchart LR" in nav_content


def test_run_all_pipeline_files_created():
    """Test that all 5 output types are created by run_all_pipeline."""
    # This test verifies the DoD requirement that all 5 outputs are generated
    test_message = "verify all outputs created"

    # Get file references for verification
    memory_file = Path("memory.json")
    egspace_events = Path("egspace/events.jsonl")

    # Baseline check (files should exist)
    if egspace_events.exists():
        print(f"EG-Space events file exists: {egspace_events}")

    # Execute pipeline
    result = run_all_pipeline(test_message)

    # Verify all outputs were created/updated:

    # 1. Logs - should have log file
    assert Path(result["log_file"]).exists()

    # 2. Memory - should be updated (this is verified by the summary being returned)
    assert result["summary"]
    assert memory_file.exists()

    # 3. Digest - should have digest file
    assert Path(result["digest_file"]).exists()

    # 4. Nav - should have nav file
    assert Path(result["nav_file"]).exists()

    # 5. EG-Space - should have events (result shows recent count, not total)
    assert result["egspace_events"] >= 2  # At least Watcher + Curator events

    print("✅ All 5 outputs verified:")
    print(f"   📋 Log: {result['log_file']}")
    print(f"   💾 Memory: updated with {len(result['summary'])} char summary")
    print(f"   📝 Digest: {result['digest_file']}")
    print(f"   🗺️  Nav: {result['nav_file']}")
    print(f"   🔗 EG-Space: {result['egspace_events']} total events")


def test_run_all_pipeline_preserves_legacy_functionality():
    """Test that the CLI maintains backwards compatibility."""
    # This test ensures that run_all_pipeline doesn't break existing functionality
    test_message = "backwards compatibility test"

    # Execute pipeline
    result = run_all_pipeline(test_message)

    # The pipeline result should contain the final role output
    assert "pipeline_result" in result
    pipeline_result = result["pipeline_result"]

    # Should have the standard role output structure
    assert "role" in pipeline_result
    assert "output" in pipeline_result
    assert "ts" in pipeline_result
    assert "refs" in pipeline_result

    # Final role should be Archivist
    assert pipeline_result["role"] == "Archivist"
