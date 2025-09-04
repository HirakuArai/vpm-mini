#!/bin/bash
# P2-2 完了処理（証跡コミット → STATE更新 → PR更新/自動マージ）
set -euo pipefail
REPO="/Users/hiraku/projects/vpm-mini"
BR="feat/p2-2-hello-ai"
EV="reports/p2_2_ai_enabled_success.md"

cd "$REPO"
git fetch origin
git checkout -B "$BR" || git checkout "$BR"

# 1) 直近の証跡ファイルを確認（無ければ中断）
test -s "$EV" || { echo "[x] Evidence not found: $EV"; exit 1; }

# 2) STATE に P2-2 GREEN を追記（main版を土台に再生成して競合回避）
git show origin/main:STATE/current_state.md > /tmp/state_main.md || cp STATE/current_state.md /tmp/state_main.md

cat >> /tmp/state_main.md <<EOF

### Phase 2 – P2-2 Hello-AI（Knative Service）
- Status: **GREEN**
- Evidence: \`${EV}\`
- Decision Log:
  - 画像を \`ko.local/hello-ai:dev\` に固定（tag-resolve skip + kind load）
  - .env の \`OPENAI_API_KEY\` を Secret 取り込み
  - \`AI_ENABLED=true\` で 200 応答・**X-Fallback:false** を確認（OpenAI 実コール成立）
EOF

mv /tmp/state_main.md STATE/current_state.md

# 3) 代表変更ファイルをステージング（アプリ/マニフェスト/証跡/STATE）
git add \
  cells/hello-ai/app.py cells/hello-ai/requirements.txt \
  infra/k8s/overlays/dev/hello-ai-ksvc.yaml infra/k8s/overlays/dev/hello-ai-cm.yaml \
  "$EV" STATE/current_state.md || true

git commit -m "feat(p2-2): hello-ai real-call established (X-Fallback=false) + evidence + STATE update" || echo "[i] nothing to commit"
git push -u origin "$BR"

# 4) PRを作成/更新 → Auto-merge（チェックGreenで自動）
if command -v gh >/dev/null 2>&1; then
  PRNUM=$(gh pr list --head "$BR" --state open --json number -q '.[0].number' || true)
  if [[ -z "$PRNUM" ]]; then
    PRNUM=$(gh pr create --base main --head "$BR" \
      -t "feat(p2-2): hello-ai real-call + evidence" \
      -b "Evidence: ${EV}"$'\n'"DoD: READY=True / 200 / X-Fallback:false" \
      --json number -q .number)
  else
    gh pr edit "$PRNUM" -b "Evidence: ${EV}"$'\n'"DoD: READY=True / 200 / X-Fallback:false"
  fi
  gh pr merge "$PRNUM" --auto --squash || true
  echo "[i] PR #$PRNUM を Auto-merge 待ちにしました。"
else
  echo "[!] gh CLI なし。PRはGitHub上で main にマージしてください。"
fi

echo "[✓] P2-2 完了処理を実行しました。PRが統合されたら P2-3（CI/SSOT 結線）へ進めます。"