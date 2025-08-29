⏺ ✅ Runbook/Alerts 更新完了

Date: 2025-08-29T01:52:18Z
Commit: 1bf742f

## 更新内容

### docs/runbooks/http_slo_999.md
- Deploy Freeze/Unfreeze 手順追加
- Post-Promotion Guard 初動対応追加

### docs/alerts.md (新規作成)
- SLO 99.9% アラート一覧
- Burn rate 基準値と severity 定義
- Runbook リンクと Alertmanager ルーティング

## アラート体系

| Alert | 窓 | Burn rate | Severity |
|---|---:|---:|---|
| SLOFastBurn | 5m | ≈14.4x | page |
| SLOSlowBurn | 30m | ≈6x | ticket |
| SLOTrendWarn | 1h | ≈3x | warn |

## 運用手順
1. Freeze/Unfreeze による CD パイプライン制御
2. Guard 失敗時の自動ロールバック対応
3. Issue 起票からの復旧フロー

→ Phase 6 運用準備完了
