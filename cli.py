#!/usr/bin/env python
"""
VPM-Mini CLI - 5-role processing pipeline with EG-Space integration

Usage:
  python cli.py run-all <message>     - Execute full pipeline: log→memory→digest→nav→egspace
  python cli.py <objective_id> <message>  - Legacy OpenAI interaction

Examples:
  python cli.py run-all "implement feature X with decision Y"
  python cli.py demo "こんにちは"
"""

import sys
import pathlib
from datetime import datetime
from pathlib import Path

# Add paths for imports
root_path = pathlib.Path(__file__).resolve().parent
sys.path.append(str(root_path / "src"))
sys.path.append(str(root_path))

# Import modules after path setup
try:
    from core import ask_openai
    from vpm_mini.logs import append_chatlog
    from vpm_mini.summary import summarize_last_session, prepend_memory
    from vpm_mini.digest import write_outputs, build_session_digest
    from src.egspace.store import get_recent_events
    from playground import run_once
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def run_all_pipeline(message: str) -> dict:
    """Execute the full end-to-end pipeline: log→memory→digest→nav→egspace."""
    print(f"🚀 Starting full pipeline for: {message}")

    # Step 1: Run 5-role pipeline (generates EG-Space events)
    print("📋 Step 1: Running 5-role pipeline...")
    pipeline_result = run_once(message)

    # Step 2: Append to chat log
    print("💾 Step 2: Logging to JSONL...")
    session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_turns = [
        {"ts": datetime.now().timestamp(), "role": "user", "text": message, "refs": []},
        {
            "ts": datetime.now().timestamp(),
            "role": "assistant",
            "text": pipeline_result.get("output", "Pipeline completed"),
            "refs": pipeline_result.get("refs", []),
        },
    ]
    log_file = append_chatlog(log_turns, session_id)

    # Step 3: Generate summary and update memory.json
    print("🧠 Step 3: Generating summary for memory.json...")
    summary = summarize_last_session(message, 400)
    prepend_memory(summary)

    # Step 4: Generate digest and nav
    print("📊 Step 4: Generating digest and nav...")
    digest_state = build_session_digest(message)
    docs_path = Path("docs/sessions")
    diagrams_path = Path("diagrams/src")
    digest_file, nav_file = write_outputs(digest_state, docs_path, diagrams_path)

    # Step 5: Verify EG-Space events were created
    print("🔗 Step 5: Verifying EG-Space integration...")
    recent_events = get_recent_events(5)
    egspace_count = len(recent_events)

    result = {
        "message": message,
        "pipeline_result": pipeline_result,
        "summary": summary,
        "log_file": str(log_file),
        "digest_file": str(digest_file),
        "nav_file": str(nav_file),
        "egspace_events": egspace_count,
        "recent_vec_ids": [e.get("vec_id", "") for e in recent_events[-3:]],
    }

    print("✅ Pipeline completed successfully!")
    print(f"   📋 Log: {log_file}")
    print(f"   📝 Digest: {digest_file}")
    print(f"   🗺️  Nav: {nav_file}")
    print(f"   🔗 EG-Space events: {egspace_count}")
    print(f"   💾 Memory updated with summary: {summary[:80]}...")

    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "run-all":
        if len(sys.argv) < 3:
            print("Usage: python cli.py run-all <message>")
            sys.exit(1)

        message = " ".join(sys.argv[2:])
        try:
            run_all_pipeline(message)
            print(f"\n🎉 Full pipeline execution completed for: '{message}'")
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            sys.exit(1)

    elif len(sys.argv) >= 3:
        # Legacy mode: objective_id + message
        obj_id = command
        user_msg = " ".join(sys.argv[2:])
        print(ask_openai(obj_id, user_msg))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
