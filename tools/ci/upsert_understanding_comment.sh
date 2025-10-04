#!/usr/bin/env bash
set -euo pipefail
: "${GH_TOKEN:?GH_TOKEN is required}"
PRNUM="${1:-}"
[ -z "$PRNUM" ] && exit 0
MARK="<!--UNDERSTANDING-GUARD-COMMENT-->"
BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'MD'
<!--UNDERSTANDING-GUARD-COMMENT-->
🧭 **Understanding — Status**
- Snapshot: {{SNAPSHOT}}
- Diag Missing: {{DIAG_MISSING}}
- Goals Equal: **{{GOALS_EQUAL}}**

Evidence: {{EVIDENCE_PATH}}

_Dry-Run:_ guard-required: **{{DRY_GUARD}}**, snapshot-present: **{{DRY_SNAP}}**, goals-synced: **{{DRY_GOAL}}**
MD
sed -i.bak \
  -e "s/{{SNAPSHOT}}/${SNAPSHOT:-n\/a}/" \
  -e "s/{{DIAG_MISSING}}/${DIAG_MISSING:-none}/" \
  -e "s/{{GOALS_EQUAL}}/${GOALS_EQUAL:-unknown}/" \
  -e "s|{{EVIDENCE_PATH}}|${EVIDENCE_PATH:-n/a}|" \
  -e "s/{{DRY_GUARD}}/${DRY_GUARD:-0}/" \
  -e "s/{{DRY_SNAP}}/${DRY_SNAP:-0}/" \
  -e "s/{{DRY_GOAL}}/${DRY_GOAL:-0}/" \
  "$BODY_FILE"

CID="$(gh issue comments "$PRNUM" --limit 100 --json id,body \
      -q 'map(select(.body|contains("<\!--UNDERSTANDING-GUARD-COMMENT-->")))[0].id' || true)"
if [ -n "${CID:-}" ]; then
  gh api repos/{owner}/{repo}/issues/comments/"$CID" -X PATCH -f body@"$BODY_FILE" >/dev/null
else
  gh pr comment "$PRNUM" -F "$BODY_FILE" >/dev/null
fi
rm -f "$BODY_FILE" "$BODY_FILE.bak"
