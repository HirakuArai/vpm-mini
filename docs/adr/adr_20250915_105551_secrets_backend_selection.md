# ADR: Secrets backend selection (P5-4)

## Status
Proposed

## Context
- Trial: K8s Secret / SOPS PoC（Gitに秘匿は載せない）
- Production: 鍵レス認証 + 監査（IAM / Workload Identity / Managed Identity / Vault Auth）

## Decision Options
- AWS Secrets Manager (+ IRSA)
- GCP Secret Manager (+ Workload Identity)
- Azure Key Vault (+ Managed Identity)
- HashiCorp Vault (+ Kubernetes Auth)

## Decision Criteria
- 最小権限（鍵レス） / 監査容易性 / 既存インフラ親和性 / 運用コスト / 料金

## Decision
- T.B.D.（次セッションで確定）

## Consequences
- SecretStore/ClusterSecretStore + ExternalSecret を provider に応じて適用
- ローテーション試験を Evidence へ記録し、SOPS PoC を撤去

## Rollout Plan
1) Secret backend 選定（ADRを決定状態へ）
2) (Cluster)SecretStore（鍵レス認証）作成
3) ExternalSecret 1本（例: am-slack-receiver）を同期
4) ローテーション試験（反映時間/挙動の記録）
5) SOPS PoC の撤去と README/STATE 更新
