#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HANDOFF="$ROOT/ops/agent_handoff/task.json"
HISTDIR="$ROOT/ops/agent_handoff/history"
RUNLOGS="$ROOT/ops/agent_handoff/task_runs.ndjson"
REPODIR="$ROOT/reports"

TS=$(date -u +%Y%m%d_%H%M%S)
RUN_ID="run_${TS}"
LOG="$REPODIR/codex_run_${TS}.log"

# jq が必要です（ローカルにインストールされていることを確認してください）
command -v jq >/dev/null || { echo "[ERR] jq is required"; exit 1; }
[[ -f "$HANDOFF" ]] || { echo "[ERR] $HANDOFF not found"; exit 1; }

mkdir -p "$HISTDIR" "$REPODIR"

# meta.dry_run および meta.use_codex を取得
DRY=$(jq -r '.meta.dry_run // false' "$HANDOFF" || echo false)
USE_CODEX=$(jq -r '.meta.use_codex // false' "$HANDOFF" || echo false)

echo "[INFO] executing: dry_run=$DRY use_codex=$USE_CODEX run_id=$RUN_ID"

if [[ "$USE_CODEX" == "true" ]] && command -v codex >/dev/null; then
  # codex CLI を使って実行
  if [[ "$DRY" == "true" ]]; then
    codex run -f "$HANDOFF" --dry-run | tee "$LOG"
  else
    codex run -f "$HANDOFF" | tee "$LOG"
  fi
else
  # codex CLI を使わない場合：Claude Code への指示
  cat "$HANDOFF" | pbcopy
  echo "[INFO] task.json をクリップボードにコピーしました。"
  if [[ "$DRY" == "true" ]]; then
    echo "[ACTION] VS Code の Claude Code 拡張に貼り付けて、次を実行してください:"
    echo "Execute this task.json as dry-run (diff only)."
  else
    echo "[ACTION] VS Code の Claude Code 拡張に貼り付けて、次を実行してください:"
    echo "Execute this task.json (apply, test, PR)."
  fi
  # Claude Code 手動実行時はログファイルを空で作成
  : > "$LOG"
fi

# 実行後にスナップショットを保存
SNAP="$HISTDIR/task_${TS}.json"
cp "$HANDOFF" "$SNAP"

# 実行ステータスを判定（エラーが含まれていれば error）
STATUS="ok"
grep -q "\[ERROR\]\|\bERROR\b" "$LOG" && STATUS="error" || true

# 実行メタを NDJSON に追記
jq -n --arg id "$RUN_ID" \
      --arg ts "$TS" \
      --arg dry "$DRY" \
      --arg snap "ops/agent_handoff/history/$(basename "$SNAP")" \
      --arg log "reports/$(basename "$LOG")" \
      --arg status "$STATUS" \
      '{run_id:$id, ts:$ts, dry_run:($dry=="true"), snapshot:$snap, log:$log, status:$status}' \
   >> "$RUNLOGS"

# _latest_index.md の更新
INDEX="$REPODIR/_latest_index.md"
{
  echo "# Hand-off Latest Index"
  echo "- run_id: $RUN_ID"
  echo "- timestamp (UTC): $TS"
  echo "- snapshot: ops/agent_handoff/history/$(basename "$SNAP")"
  echo "- log: reports/$(basename "$LOG")"
  echo "- status: $STATUS"
} > "$INDEX"

# latest.json へのシンボリックリンクを更新
ln -sf "$(basename "$SNAP")" "$HISTDIR/latest.json"

echo "[INFO] snapshot: $SNAP"
echo "[INFO] log     : $LOG"
echo "[INFO] index   : $INDEX"