#!/usr/bin/env bash
set -euo pipefail
f=$(ls -1 reports/evidence_kservice_ready_*.md reports/p2_2_hello_ksvc_*.md 2>/dev/null | tail -n1 || true)
[ -n "$f" ] || { echo "No evidence file found"; exit 1; }

if grep -Eq 'Result:[[:space:]]*PASS|READY status extracted:[[:space:]]*"True"|READY:[[:space:]]*"True"|Ready:[[:space:]]*True' "$f"; then
  echo "DoD OK: $f"
else
  echo "DoD fail: READY not True in $f"; exit 1
fi