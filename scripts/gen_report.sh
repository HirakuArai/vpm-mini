#!/usr/bin/env bash
set -euo pipefail
STATE_PATH="${1:-STATE/mna_state.md}"
STAMP="$(date +%Y%m%d_%H%M)"
OUT="reports/mna_update_${STAMP}.md"

mkdir -p reports

if command -v codex >/dev/null 2>&1; then
  codex run --prompt-file prompts/state_to_plan.md --in "$STATE_PATH" --out "$OUT"
else
  # codex が無い場合のフォールバック
  python3 scripts/codex_shim.py \
    --prompt-file prompts/state_to_plan.md \
    --in "$STATE_PATH" \
    --out "$OUT"
fi

# ICR履歴を追記（失敗しても処理継続）
bash scripts/append_icr_csv.sh "$OUT" || true

# グラフを更新（失敗しても処理継続）
python3 scripts/plot_icr.py reports/icr_history.csv reports/icr_history.png || true

echo "Report generated: $OUT"