#!/usr/bin/env bash
set -euo pipefail
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
SHA="${1:-${GITHUB_SHA:-}}"
if [ -z "$SHA" ]; then
  SHA="${GITHUB_HEAD_SHA:-${GITHUB_SHA:-}}"
fi
end=$((SECONDS+180))
DG=0; DS=0; DG2=0
while [ $SECONDS -lt $end ]; do
  JSON="$(gh api repos/{owner}/{repo}/commits/$SHA/status --jq '[.statuses[]?|{context,state}]' 2>/dev/null || echo '[]')"
  ok(){ printf '%s' "$JSON" | jq -r --arg k "$1" '[ .[] | select(.context==$k and .state=="success") ] | length'; }
  DG="$(ok 'understanding/guard-required' || echo 0)"
  DS="$(ok 'understanding/snapshot-present' || echo 0)"
  DG2="$(ok 'understanding/goals-synced' || echo 0)"
  if [ "${DG:-0}" -ge 1 ] && [ "${DS:-0}" -ge 1 ] && [ "${DG2:-0}" -ge 1 ]; then
    break
  fi
  sleep 3
done
{
  echo "dry_guard=${DG:-0}"
  echo "dry_snap=${DS:-0}"
  echo "dry_goal=${DG2:-0}"
} >> "$GITHUB_OUTPUT"
