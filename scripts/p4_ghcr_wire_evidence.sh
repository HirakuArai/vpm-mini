#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_ghcr_wire_${TS}.md"
echo "# P4 GHCR Wiring Evidence (${TS})" | tee "$R"
echo "## Argo: apply hello-ai app" | tee -a "$R"
kubectl -n argocd apply -f infra/argocd/apps/hello-ai-app.yaml | sed 's/^/  /' | tee -a "$R" || true
echo "## Argo apps" | tee -a "$R"
kubectl -n argocd get applications -o wide | sed 's/^/  /' | tee -a "$R" || true