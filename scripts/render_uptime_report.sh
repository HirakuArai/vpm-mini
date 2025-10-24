#!/usr/bin/env bash
set -euo pipefail
WF_NAME=${WF_NAME:-"Render Daily (07:00 JST)"}
LIMIT=${LIMIT:-7}
OUT="reports/render_daily_uptime_$(date +%Y%m%d).md"

echo "# Render Daily Uptime (last ${LIMIT} runs)" > "$OUT"; echo >> "$OUT"
runs_json=$(gh run list --workflow "$WF_NAME" --limit "$LIMIT" --json databaseId,htmlUrl,displayTitle,createdAt)
total=$(echo "$runs_json" | jq 'length'); ok=0
echo "## Runs" >> "$OUT"; echo >> "$OUT"
for row in $(echo "$runs_json" | jq -r 'to_entries[] | @base64'); do
  _jq(){ echo "$row" | base64 --decode | jq -r "$1"; }
  id=$(_jq '.value.databaseId'); url=$(_jq '.value.htmlUrl'); title=$(_jq '.value.displayTitle'); created=$(_jq '.value.createdAt')
  TMP=$(mktemp -d)
  if gh run download "$id" -n grafana-render -D "$TMP" >/dev/null 2>&1; then
    ev=$(fd -a evidence.log "$TMP" | head -n1 || true)
    if [ -n "${ev:-}" ] && tail -n1 "$ev" | grep -q "== FOOTER == OK"; then
      echo "- ✅ [OK] [Run #$id]($url) — $title ($created)" >> "$OUT"; ok=$((ok+1))
    else
      echo "- ❌ [NG] [Run #$id]($url) — $title ($created)" >> "$OUT"
      ng_body="Render daily NG\nRun: $url\nTitle: $title\nCreated: $created\nEvidence tail:\n$( ( [ -n \"${ev:-}\" ] && tail -n3 \"$ev\" ) || echo '(no evidence.log)')"
      issue_url=$(gh issue create --title "Render Daily NG: Run #$id" --body "$ng_body" --label evidence --label render --assignee @me | tail -n1)
      echo "  - Issue: $issue_url" >> "$OUT"
    fi
  else
    echo "- ❌ [NG] [Run #$id]($url) — $title ($created) (no artifacts)" >> "$OUT"
  fi
  rm -rf "$TMP"
done
rate=$(( total>0 ? 100*ok/total : 0 ))
{
  echo; echo "## Summary"; echo
  echo "- OK: $ok / $total"
  echo "- Uptime (7 runs): ${rate}%"; echo
  [ "$rate" -ge 95 ] && echo "**Status: GREEN**" || echo "**Status: YELLOW/RED**"
} >> "$OUT"
echo "$OUT"
