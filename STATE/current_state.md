# この文書の役割
本プロジェクトでは、事象目的空間における **現在地（C）**、**ゴール（G）**、および **δ（差分）** を常に把握し、次アクションを明確化する。

---

## 状態宣言 (SSOT)
```yaml
active_repo: vpm-mini
active_branch: main
phase: Phase 6   # Global Resilience & Scale
context_header: "repo=vpm-mini / branch=main / phase=Phase 4"
short_goal: "マルチクラスタのグローバル配信 + 30日連続 SLO 99.9%"
exit_criteria:
  - GSLB/Edge で multi-cluster ルーティング（自動フェイルオーバー）
  - GitOps 完全自動（PR→Canary→昇格→Post-Guard）を multi-cluster に展開
  - 30日連続 SLO 99.9%（アラート/Runbook/自動回復の運用実績）
