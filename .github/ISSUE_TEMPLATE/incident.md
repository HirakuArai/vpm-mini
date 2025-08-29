---
name: Incident Report
about: Post-Guard failure / SLO alert firing
title: "[INCIDENT] <short summary>"
labels: incident
assignees: ""
---

## 概要
- **事象開始**: <!-- JST/UTC -->
- **影響範囲**: <!-- users/requests/services -->
- **監視イベント**: <!-- SLOFastBurn / SlowBurn / Guard NG など -->

## 初動 / 一時対応
- **切戻し / Freeze 実施**: <!-- yes/no & 時刻 -->
- **連絡**: <!-- oncall/slack -->

## 技術詳細
- **直近の変更**: <!-- PR/タグ -->
- **メトリクス**: <!-- p50/p95/success/CPU/Mem など -->
- **ログ断片**: <!-- 重要行リンク or 添付 -->

## 原因分析（仮説 → 確定）
- **根本原因**:
- **再発条件**:

## 対応
- **暫定対応**:
- **恒久対応**:
- **解除手順（Unfreeze など）**:

## 証跡リンク
- **reports/phase5_cd_guard_result.json**:
- **reports/phase4_canary_promotion.json**:
- **dashboards / runbooks**:

## Timeline
| 時刻 | 事象 | 対応者 |
|------|------|--------|
|      |      |        |

## Post-Mortem
- [ ] 根本原因特定完了
- [ ] 恒久対策実施完了  
- [ ] Runbook/Alert 改善完了
- [ ] チーム共有完了
