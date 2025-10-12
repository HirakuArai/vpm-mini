#!/usr/bin/env bash
set -euo pipefail

ts=$(date +%Y%m%d_%H%M%S)
report="reports/p2_1_bootstrap_${ts}.md"
mkdir -p reports

echo "# P2-1 bootstrap (${ts})" > "$report"

kind get clusters | grep -q vpm-mini || kind create cluster --name vpm-mini

KN_VER="1.18.0"
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KN_VER}/serving-crds.yaml"
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KN_VER}/serving-core.yaml"
kubectl apply -f "https://github.com/knative/net-kourier/releases/download/knative-v${KN_VER}/kourier.yaml"

kubectl wait deploy -n knative-serving --all --for=condition=Available --timeout=180s
kubectl wait deploy -n kourier-system --all --for=condition=Available --timeout=180s

kubectl patch configmap/config-domain -n knative-serving \
  --type merge -p '{"data": {"127.0.0.1.sslip.io": ""}}' || true

{
  echo "## Checks"
  echo '```'
  kubectl get deploy -n knative-serving
  kubectl get deploy -n kourier-system
  echo '```'
  echo "✅ P2-1 GREEN (serving+kourier available)"
} >> "$report"
