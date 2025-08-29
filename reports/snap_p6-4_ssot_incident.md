⏺ ✅ SSOT追補 + Incidentテンプレ追加

Date: 2025-08-29T03:09:31Z  
Commit: d9e910f

## 更新内容

### diagrams/src/ops_single_source_of_truth_v1.md
**Phase 5+ 運用ループ追補:**
- CD Canary: 90/10 → 50/50 → 100/0 (SLOゲート)
- Post-Guard: 監視ウィンドウ → Rollback/Freeze/Issue
- Multi-Cluster GitOps: ApplicationSet で a/b 同期
- Edge Failover: HAProxy/DNS 自動切替
- Mermaid フローチャートで視覚化

### .github/ISSUE_TEMPLATE/incident.md (新規)
**インシデント管理テンプレート:**
- 概要: 事象開始、影響範囲、監視イベント
- 初動対応: 切戻し/Freeze、連絡体制
- 技術詳細: 変更履歴、メトリクス、ログ
- 原因分析: 根本原因、再発条件
- 対応手順: 暫定/恒久、Unfreeze
- 証跡リンク: JSON、ダッシュボード、Runbook
- Timeline: 時系列記録
- Post-Mortem: チェックリスト

## 運用体制強化
- **SSOT**: Phase 5+ の運用ループを明文化
- **インシデント管理**: 構造化されたテンプレート
- **証跡管理**: reports/ ディレクトリとの連携
- **チーム連携**: 標準化された報告形式

→ Phase 6 インシデント管理体制 完備
