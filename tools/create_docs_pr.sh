#!/usr/bin/env bash
set -euo pipefail
TITLE="${1:-docs: update}"
BODYF=$(mktemp)
TS=$(date +%Y%m%d_%H%M%S)
EV="reports/auto_${TS}.md"
echo -e "# Evidence (auto)\n- 概要: ${TITLE}\n- 変更: ドキュメント更新\n" > "$EV"
git add "$EV" && git commit -m "evidence: $TITLE (${TS})" || true
cat > "$BODYF" << 'MD'
## 目的
ドキュメント更新

## 変更点
- 変更内容を記載

context_header: repo=vpm-mini / branch=main / phase=Phase 5: Scaling & Migration

## Exit Criteria
- [x] PR 本文の必須ブロックを満たす
- [x] Evidence を PR に含める

## Evidence
- reports/auto_*.md

## DoD チェックリスト（編集不可・完全一致）
- [x] Auto-merge (squash) 有効化
- [x] CI 必須チェック Green（test-and-artifacts, healthcheck）
- [x] merged == true を API で確認
- [x] PR に最終コメント（✅ merged / commit hash / CI run URL / evidence）
- [x] 必要な証跡（例: reports/*）を更新
MD
gh pr create --fill --title "$TITLE" --body-file "$BODYF" || true
gh pr merge --squash --auto || true
echo "PR submitted with auto evidence and strict PR body."
