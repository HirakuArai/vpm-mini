#!/usr/bin/env bash
set -euo pipefail
: "${GH_TOKEN:?GH_TOKEN is required}"
PRNUM="${1:-}"
[ -z "$PRNUM" ] && exit 0

BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'MD'
<!--UNDERSTANDING-GUARD-COMMENT-->
🧭 **Understanding — Status**
- Snapshot: {{SNAPSHOT}}
- Diag Missing: {{DIAG_MISSING}}
- Goals Equal: **{{GOALS_EQUAL}}**

Evidence: {{EVIDENCE_PATH}}
MD

sed -i.bak \
  -e "s/{{SNAPSHOT}}/${SNAPSHOT:-n\/a}/" \
  -e "s/{{DIAG_MISSING}}/${DIAG_MISSING:-none}/" \
  -e "s/{{GOALS_EQUAL}}/${GOALS_EQUAL:-unknown}/" \
  -e "s|{{EVIDENCE_PATH}}|${EVIDENCE_PATH:-n/a}|" \
  "$BODY_FILE"

mapfile -t MATCH_IDS < <(gh api repos/{owner}/{repo}/issues/"$PRNUM"/comments --paginate \
  --jq 'map(select(.body | contains("<!--UNDERSTANDING-GUARD-COMMENT-->") )) | map(.id) | .[]' 2>/dev/null || true)
CID="${MATCH_IDS[0]:-}"
if [ -n "$CID" ]; then
  gh api repos/{owner}/{repo}/issues/comments/"$CID" -X PATCH -f body="$(cat "$BODY_FILE")" >/dev/null
  if [ "${#MATCH_IDS[@]}" -gt 1 ]; then
    for DUP in "${MATCH_IDS[@]:1}"; do
      gh api repos/{owner}/{repo}/issues/comments/"$DUP" -X DELETE >/dev/null || true
    done
  fi
else
  gh pr comment "$PRNUM" -F "$BODY_FILE" >/dev/null
fi
rm -f "$BODY_FILE" "$BODY_FILE.bak"
