⏺ ✅ Multi-Cluster & Edge/Failover ドキュメント追加

Date: 2025-08-29T02:51:20Z  
Commit: 2621508

## 追加ドキュメント

### docs/multicluster/apps.md
- ApplicationSet によるマルチクラスター GitOps 運用
- クラスタ登録とラベル付与手順
- NodePort差別化（cluster-a: 31380, cluster-b: 32380）
- ゼロタッチ展開による新クラスタ自動検出
- 検証: scripts/phase5_appset_verify.sh

### docs/edge/failover.md  
- HAProxy による Edge L7 フェイルオーバー実演
- cluster-a → cluster-b 自動切替手順
- エンドポイント: localhost:30080 (統一入口)
- 検証基準: RTO≤60s, 成功率≥95%, P50<1000ms
- 本番GSLB/DNS置換への移行指針

## 運用体制
- **マルチクラスター**: ApplicationSet ゼロタッチ展開
- **フェイルオーバー**: 自動切替 + SLA維持
- **監査**: JSON証跡保存（reports/phase5_*.json）

## 技術スタック
- Argo CD ApplicationSet (multi-cluster sync)
- HAProxy (Edge L7 failover)  
- Istio (service mesh routing)
- Kubernetes NodePort (differentiation)

→ Phase 6 グローバル配信基盤 文書化完了
