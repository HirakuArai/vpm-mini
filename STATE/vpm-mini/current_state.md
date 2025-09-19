# === State Declaration (Single Source of Truth) ===
active_repo: vpm-mini
active_branch: main
phase: Phase 2
context_header: "repo=vpm-mini / branch=main / phase=Phase 2"
short_goal: "Phase 2 Kickoff (kind + Knative 足場構築)"
exit_criteria:
  - "P2-1 GREEN: kind + Knative (v1.18) 足場構築スクリプトが動作"
  - "P2-2 GREEN: Hello KService デプロイ成功 (kubectl get ksvc hello → READY=True)"
updated_at: 2025-09-19T00:00+09:00

## Phase Progress
- **P1** (Foundation): ✅ GREEN  
- **P2** (Chaos Engineering): ✅ GREEN
- **P3** (Advanced Chaos): ✅ GREEN  
- **P4** (GitOps + ArgoCD): ✅ GREEN
- **P5** (Scaling & Migration): 🟡 IN_PROGRESS

## P5 Sub-phases
- **P5-1** (Autoscaling PoC): ✅ GREEN
- **P5-2** (Minimal UI): ✅ GREEN  ← 🆕 UPDATED
- **P5-3** (Compose→Knative): ✅ GREEN
- **P5-4** (Secrets with Vault): ✅ GREEN  ← 🆕 UPDATED  
- **P5-5** (Consumer Injection): ⏳ NEXT
- **P5-6** (Observability Line): ⏳ PENDING

## Current Focus: P5-5 Consumer Injection
**Goal**: secretKeyRef integration with Vault-synced secrets
- Move from ExternalSecret demo to real consumer workloads
- Inject vault-synced secrets into KServices via secretKeyRef
- Evidence: secret consumption in running pods

## Evidence Reports
- P5-2 UI: reports/ui_manual_evidence_20250916_153047.md
- P5-4 Vault: reports/p5_4_secrets_vault_verify_20250916_171916.md


## 優先タスク
- P2-1: kind + Knative 足場構築（infra/kind-dev/kind-cluster.yaml、scripts/p2_bootstrap_kind_knative.sh、CIバリデーション）
- P2-2: Hello KService デプロイ（infra/k8s/overlays/dev/hello-ksvc.yaml、READY=True証跡）

Updated: 2025-09-16T20:23:15Z
