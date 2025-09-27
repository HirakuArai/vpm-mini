#!/usr/bin/env bash
set -euo pipefail

KN_VER="v1.18.0"

echo "=== Install Knative Serving ${KN_VER} on kind cluster ==="
kubectl get nodes

# CRDs & Core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-${KN_VER}/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-${KN_VER}/serving-core.yaml

# Kourier
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-${KN_VER}/kourier.yaml

# Use kourier as default ingress
kubectl patch configmap/config-network \
  -n knative-serving \
  -p='{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'

# (任意) ローカル解決用のドメイン
kubectl patch configmap/config-domain -n knative-serving \
  --type merge -p='{"data":{"127.0.0.1.sslip.io":""}}' || true

echo "=== Wait for knative-serving & kourier to be Available ==="
kubectl -n knative-serving wait deploy --all --for=condition=Available --timeout=5m
kubectl -n kourier-system  wait deploy --all --for=condition=Available --timeout=5m

echo "Knative bootstrap done."
