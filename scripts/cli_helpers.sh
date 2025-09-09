set -euo pipefail
# main を最新化
update_main() {
  git fetch origin
  git switch main
  git pull --ff-only
}
# 新規ブランチを安全に作る（必ず最新 main から）
new_branch() {
  local BR="$1"; update_main; git switch -c "$BR"
}
# push 後に必ず PR を作って auto-merge を予約（既にPRがあればそれを使う）
ensure_pr() {
  local TITLE="$1"; shift
  local BODY="${1:-}"; shift || true
  local HEAD; HEAD=$(git rev-parse --abbrev-ref HEAD)
  local N; N=$(gh pr list --head "$HEAD" --state open --json number -q '.[0].number' 2>/dev/null || true)
  if [ -z "${N:-}" ]; then
    local URL; URL=$(gh pr create --base main --title "$TITLE" --body "$BODY")
    N="${URL##*/}"
  fi
  gh pr merge "$N" --auto --squash || true
}
