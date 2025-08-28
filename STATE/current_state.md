# この文書の役割
本プロジェクトでは、事象目的空間における **現在地（C）**、**ゴール（G）**、および **δ（差分）** を常に把握し、次アクションを明確化する。

---

## 状態宣言 (SSOT)
```yaml
active_repo: vpm-mini
active_branch: main
phase: Phase 4
context_header: "repo=vpm-mini / branch=main / phase=Phase 4"
short_goal: "Istio + Gateway API / Argo CD の足場構築"
exit_criteria:
  - "800 cells/sec 耐性 (短時間)"
  - "Live A/B の評価枠組み起動"
  - "SLO 99% 維持"
updated_at: 2025-08-28T20:40:00+0900
```

## 現在地（C）
- Phase 3 完了（tag: phase3-complete）
- SPIFFE/SPIRE でセル固有 ID 付与完了
- OPA Gatekeeper / NetworkPolicy でポリシー強制
- W3C PROV 準拠の決定ログ保存（署名付き S3）
- Chaos/監査シナリオで SLO 99% 維持済み

## ゴール（G）— Phase 4
- Istio + Gateway API による高度ルーティング
- ArgoCD による GitOps デプロイメント足場
- A/B テスト評価枠組みの構築
- 800 cells/sec 大規模負荷耐性の確立

## 差分（δ）と次アクション
- δ: 大規模運用・高度デプロイメント機能が未導入
- 次アクション:
  - Step 4-1: Istio + Gateway API 足場（Hello ルート疎通）
  - Step 4-2: ArgoCD 導入と GitOps 足場
  - Step 4-3: A/B テスト評価枠組み構築
  - Step 4-4: 大規模負荷耐性確立（800 cells/sec）
