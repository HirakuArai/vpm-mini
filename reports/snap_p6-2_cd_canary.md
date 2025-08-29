⏺ ✅ CD canary pipeline ドキュメント追加

Date: 2025-08-29T02:04:14Z  
Commit: 2cb76d5

## 追加内容: docs/cd/canary_pipeline.md

### パイプラインフロー
PR/Push → ArgoCD同期 → Canary 90/10 → SLOゲート → 50/50 → SLOゲート → 100/0 → Post-Guard → Snapshot/Tag

### 主要仕様
- **トリガ**: パスベースpush / workflow_dispatch
- **SLOゲート**: N=300, p50<1000ms, success≥99%
- **Post-Guard**: 10分間監視ウィンドウ
- **失敗時**: 自動Rollback + Freeze + Issue起票

### アーティファクト
- reports/phase4_canary_promotion.json
- reports/snap_phase5-2-cd-canary.md
- タグ: phase5-2-cd-canary

### 参照ファイル
- .github/workflows/cd_canary.yml
- scripts/phase4_canary_promote.sh
- scripts/cd_guard_post_promotion.py
- docs/runbooks/http_slo_999.md

→ Phase 6 CD自動昇格パイプライン仕様 文書化完了
