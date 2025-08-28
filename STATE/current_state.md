# この文書の役割
本プロジェクトでは、事象目的空間における **現在地（C）**、**ゴール（G）**、および **δ（差分）** を常に把握し、次アクションを明確化する。

---

## 状態宣言 (SSOT)
```yaml
active_repo: vpm-mini
active_branch: main
phase: Phase 3
context_header: "repo=vpm-mini / branch=main / phase=Phase 3"
short_goal: "SPIFFE/SPIRE 導入（セル固有ID付与）"
exit_criteria:
  - "第三者監査シナリオを通過"
  - "Chaos/監査負荷下で SLO 99% 維持"
updated_at: 2025-08-29T00:45:44+0900
```

## 現在地（C）
- Phase 2 完了（tag: phase2-complete）
- kind + Knative v1.18（Kourier）/ Hello READY
- Redis / Prometheus / Grafana 稼働
- Autoscale: min=0 / max=50（簡易負荷 OK）
- KPI: p50 < 1s / JSON errors < 1%

## ゴール（G）— Phase 3
- SPIFFE/SPIRE によるセル固有 ID 付与
- OPA Gatekeeper / NetworkPolicy によるポリシー強制
- W3C PROV 準拠の決定ログ保存（署名付き S3）
- Chaos/監査シナリオで SLO 99% 維持

## 差分（δ）と次アクション
- δ: 監査性・セキュリティ制約が未適用
- 次アクション:
  - Step 3-1: SPIFFE/SPIRE 導入
  - Step 3-2: OPA Gatekeeper でスキーマ/ネットワーク制約
  - Step 3-3: 決定ログ（W3C PROV）保存
  - Step 3-4: Chaos/監査シナリオ
