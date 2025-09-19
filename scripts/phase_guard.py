#!/usr/bin/env python3
import argparse
import pathlib
import re
import sys
import os


def main():
    ap = argparse.ArgumentParser(description="Phase drift guard for STATE files")
    ap.add_argument(
        "--project",
        dest="project",
        default="vpm-mini",
        help="Project namespace (default: vpm-mini)",
    )
    args = ap.parse_args()

    # Get allowed phases from environment or default
    allowed_env = os.environ.get("PHASE_ALLOWED", "")
    if allowed_env:
        allowed_phases = [p.strip() for p in allowed_env.split(",")]
    else:
        allowed_phases = ["Phase 2"]

    # Target STATE file
    state_file = pathlib.Path(f"STATE/{args.project}/current_state.md")

    print(f"[phase-guard] checking: {state_file}", file=sys.stderr)
    print(f"[phase-guard] allowed phases: {allowed_phases}", file=sys.stderr)

    # Check if file exists
    if not state_file.exists():
        print(
            f"[phase-guard] ERROR: STATE file not found: {state_file}", file=sys.stderr
        )
        sys.exit(1)

    # Read and parse the file
    try:
        content = state_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[phase-guard] ERROR: Could not read {state_file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract phase using regex
    phase_match = re.search(r"^phase:\s*(.+)$", content, re.MULTILINE)

    if not phase_match:
        print(
            f"[phase-guard] ERROR: No phase line found in {state_file}", file=sys.stderr
        )
        print("[phase-guard] Expected format: 'phase: <phase_name>'", file=sys.stderr)
        sys.exit(1)

    current_phase = phase_match.group(1).strip()

    print(f"[phase-guard] detected phase: '{current_phase}'", file=sys.stderr)

    # Check if current phase is allowed
    if current_phase not in allowed_phases:
        print("[phase-guard] ❌ PHASE DRIFT DETECTED!", file=sys.stderr)
        print(f"[phase-guard] Current phase: '{current_phase}'", file=sys.stderr)
        print(f"[phase-guard] Allowed phases: {allowed_phases}", file=sys.stderr)
        print(f"[phase-guard] File: {state_file}", file=sys.stderr)
        print(
            "[phase-guard] Please fix the phase in STATE file to match allowed phases",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"[phase-guard] ✅ Phase validation passed: '{current_phase}'", file=sys.stderr
    )
    print(f"[phase-guard] File: {state_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
