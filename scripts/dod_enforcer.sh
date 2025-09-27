#!/usr/bin/env bash
set -euo pipefail

REPORTS_DIR="reports"
LATEST_EVIDENCE=$(ls -t "$REPORTS_DIR"/evidence_kservice_ready_*.md 2>/dev/null | head -1 || echo "")

if [ -z "$LATEST_EVIDENCE" ]; then
  echo "::error::No evidence file found in $REPORTS_DIR"
  exit 1
fi

echo "Checking DoD compliance in: $LATEST_EVIDENCE"

if grep -qE 'Ready.*:.*["\s]?True["\s]?' "$LATEST_EVIDENCE"; then
  echo "✅ DoD PASS: Ready=True found in evidence"
  exit 0
else
  echo "❌ DoD FAIL: Ready=True NOT found in evidence"
  echo ""
  echo "Evidence content:"
  cat "$LATEST_EVIDENCE"
  exit 1
fi