# === Codex Brief: Phase 4 Kickoff 準備（safe edition） ===
# 使い方：
#   SERVICE=hello DRY_RUN=0 DRAFT_PR=1 bash codex_phase4_kickoff.sh
# 既定値：SERVICE="candidate-a"、DRY_RUN=0、DRAFT_PR=0

set -euo pipefail

SERVICE="${SERVICE:-candidate-a}"
DRY_RUN="${DRY_RUN:-0}"      # 1でpush/PRを抑止（STATE生成のみ）
DRAFT_PR="${DRAFT_PR:-0}"    # 1でPRをDraftに

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
note()  { printf "\n\033[36m## %s\033[0m\n" "$*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || { red "Missing: $1"; exit 1; }; }

note "0) Sanity"
need_cmd git
need_cmd gh
git fetch origin

# 未コミットの安全確認
if ! git diff --quiet || ! git diff --cached --quiet; then
  red "Working tree is not clean. Commit/stash before running."
  git status --porcelain || true
  exit 1
fi

git switch main >/dev/null 2>&1 || git checkout main
git pull --ff-only

# gh 認証チェック
if ! gh auth status >/dev/null 2>&1; then
  red "gh is not authenticated. Run: gh auth login  （GitHub App/PATいずれか）"
  exit 1
fi

need_cmd kubectl || true
gh --version || true
kubectl version --client || true

# リポ情報
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

# Workflow IDをファイル名から解決（ハードコード回避）
note "1) 運用ライン健全性チェック（cron→自動PR→自動マージ）"
WF_FILE="render_grafana_png.yml"
WID="$(gh api "repos/$REPO/actions/workflows?per_page=100" -q \
  ".workflows[] | select(.path | contains(\"$WF_FILE\")) | .id")"
if [ -z "${WID:-}" ]; then
  red "Workflow '$WF_FILE' not found. Confirm it exists in $REPO/.github/workflows/"
  exit 1
fi
green "Resolved workflow id: $WID for $WF_FILE"

echo "### recent runs"
gh api "repos/$REPO/actions/workflows/$WID/runs?per_page=3" \
  -q '.workflow_runs[] | {id,event,status,conclusion,created_at,head_branch}'

# ラベル存在チェック（権限があれば作成）
ensure_label() {
  local label="$1" color="${2:-777777}"
  if ! gh label list --limit 300 --json name -q '.[].name' | grep -Fx "$label" >/dev/null; then
    if gh label create "$label" --color "$color" >/dev/null 2>&1; then
      green "Created label: $label"
    else
      note "Label not present and could not create: $label (permission?)"
    fi
  fi
}
ensure_label "p3-2"    "0E8A16"
ensure_label "evidence" "0366D6"
ensure_label "bot"     "5319E7"
ensure_label "state"   "6E7781"

echo "### open artifact PRs (p3-2+evidence+bot)"
gh pr list --state open   --label p3-2 --label evidence --label bot \
  --json number,title,author,mergeStateStatus --jq '.'

echo "### merged artifact PRs (latest 1)"
gh pr list --state merged --label p3-2 --label evidence --label bot \
  --limit 1 --json number,title,mergedAt --jq '.'

note "2) Phase 4 Kickoff STATE（P4-1先行）を作成"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p STATE

STATE_FILE="STATE/update_${TS}_phase4_kickoff.md"
cat > "$STATE_FILE" <<MD
# === Phase 4 Kickoff ===
context_header: "repo=vpm-mini / branch=main / phase=Phase 4 Kickoff"

## 現在地（C）
- Phase 3 完了（自動Evidenceライン/自動マージ/週次掃除が安定稼働）
- 直近Evidence: reports/p3_2_grafana_auto_render_*.md / img/grafana_p3_2_auto_*.png

## 短期ゴール（G）
- **P4-1**: Knative移植の縦スライス #1（対象サービス：${SERVICE}）
  - 最小DoD:
    - [ ] KService マニフェスト（env/secret/configの最小移植）
    - [ ] デプロイ後 READY=True
    - [ ] /metrics または主要エンドポイントの UP=1 を確認
    - [ ] Evidence（MD+PNG）と SSOT 反映、PRはAuto-merge

- **P4-2**: 外形監視(blackbox/uptime)の導入 → SLO基礎の可視化

## δ（次の一手）
- A) P4-1 の対象 ${SERVICE} を \`infra/k8s/overlays/dev/\` に雛形追加 → 動作/Evidence → 小PR
- B) P3 自動Evidenceラインを踏襲し、P4-1 のダッシュボード枠を予約

## 参照
- タグ: p3-green-20251017
- Workflows: render_grafana_png / auto_merge_evidence / weekly_artifact_cleanup
MD

green "STATE note generated: $STATE_FILE"

if [ "$DRY_RUN" = "1" ]; then
  note "DRY_RUN=1 → push/PRは行いません（STATE作成のみ）"
  exit 0
fi

# ブランチ作成＆PR
BR="chore/state-phase4-kickoff"
if ! git switch -c "$BR" 2>/dev/null; then
  git switch "$BR"
fi
git add "$STATE_FILE"
git commit -m "chore(state): Phase 4 Kickoff – goals & next steps (P4-1: ${SERVICE})"
git push -u origin HEAD

PR_FLAGS=(--fill --title "chore(state): Phase 4 Kickoff (P4-1: ${SERVICE})" --label state)
if [ "$DRAFT_PR" = "1" ]; then
  PR_FLAGS+=(--draft)
fi

gh pr create "${PR_FLAGS[@]}"
note "3) （任意）P4-1 対象サービス名を PR にコメント追記可"
echo "例: gh pr comment \$(gh pr view --json number -q .number) -b \"P4-1対象: ${SERVICE}\""

green "=== Ready: 運用ライン確認→STATE PRまで完了（SERVICE=${SERVICE}, DRY_RUN=${DRY_RUN}, DRAFT_PR=${DRAFT_PR}) ==="
