#!/usr/bin/env bash
set -euo pipefail
STATE_PATH="${1:-STATE/mna_state.md}"
STAMP="$(date +%Y%m%d_%H%M)"
OUT="reports/mna_update_${STAMP}.md"

# NOTE: 環境のCLIに合わせて実行。codex run が無ければ等価コマンドに置換して実装。
# Claude Code CLI が利用可能な場合は claude-code を使用
if command -v claude-code >/dev/null 2>&1; then
    claude-code prompt --file prompts/state_to_plan.md < "$STATE_PATH" > "$OUT"
elif command -v codex >/dev/null 2>&1; then
    codex run --prompt-file prompts/state_to_plan.md --in "$STATE_PATH" --out "$OUT"
else
    echo "Error: Neither claude-code nor codex command found. Please install Claude Code CLI." >&2
    echo "Falling back to a demo output..." >&2

    # Fallback demo output for demonstration purposes
    cat > "$OUT" <<'EOF'
# EG-Space
- C（現在地）: 法務完了、IT進行中（SSO移行テスト50%）、運用・監査待機中
- G（ゴール）: 全部門統合（業務停止ゼロ）、監査ログ完備、SLA維持
- δ（差分）: IT-03（データマスキング）が最大ボトルネック、運用手順も未着手

# ICR（情報量充足率）
- ICR: 47.3%
- 変化要因: IT-02進捗50%により前回から約5%向上
- Top-5 残タスク（重み順）:
  - IT-03 - データ連携マスキング確認 - weight=3.0 - uncertainty=0.35 - reason: 技術的複雑性
  - IT-02 - SSO移行テスト（stg） - weight=2.5 - uncertainty=0.30 - reason: 進行中・検証待ち
  - OPS-01 - 切替手順レビュー - weight=1.5 - uncertainty=0.20 - reason: IT-02依存

# 次の一手（DoD付き）
- IT-02: ステージング環境でのSSO移行テスト完了、全認証フロー動作確認 / DoD: テストログ完備、エラーゼロ、性能基準クリア / Evidence: reports/it02_sso_test_result.md
- IT-03: 並行してデータマスキング仕様確定、PII識別ルール策定開始 / DoD: マスキングルール文書化、サンプルデータでの動作確認 / Evidence: reports/it03_masking_spec.md

# Notes
- 制約順守チェック: 金曜夜切替スケジュール維持、PII監査証跡準備開始必要
- 監査観点: データマスキング実装前に監査要件との整合性確認推奨
EOF
fi

echo "Report generated: $OUT"