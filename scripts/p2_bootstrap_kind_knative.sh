#!/usr/bin/env bash
set -euo pipefail

# === Config ===
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-vpm-mini}"
KN_VERSION="${KN_VERSION:-1.18.0}"        # Knative Serving
USE_KOURIER="${USE_KOURIER:-1}"           # 1=Kourier (軽量), 0=Istio

# === Pre-check ===
command -v kind >/dev/null || { echo "kind がありません"; exit 1; }
command -v kubectl >/dev/null || { echo "kubectl がありません"; exit 1; }

# === Create cluster if not exists ===
if ! kind get clusters | grep -q "^${KIND_CLUSTER_NAME}$"; then
  if [ -f infra/kind-dev/kind-cluster.yaml ]; then
    echo "Creating kind cluster from infra/kind-dev/kind-cluster.yaml ..."
    kind create cluster --name "${KIND_CLUSTER_NAME}" --config infra/kind-dev/kind-cluster.yaml
  else
    echo "Creating kind cluster (default config) ..."
    kind create cluster --name "${KIND_CLUSTER_NAME}"
  fi
else
  echo "kind cluster '${KIND_CLUSTER_NAME}' は既に存在します（スキップ）"
fi

# === Install Knative Serving ===
echo "Installing Knative Serving v${KN_VERSION} ..."
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KN_VERSION}/serving-crds.yaml"
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KN_VERSION}/serving-core.yaml"

# === Ingress ===
if [ "${USE_KOURIER}" = "1" ]; then
  echo "Installing Kourier ..."
  kubectl apply -f "https://github.com/knative/net-kourier/releases/download/knative-v${KN_VERSION}/kourier.yaml"
  kubectl patch configmap/config-network -n knative-serving \
    -p='{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'
  # Port forward for local use (optional)
  echo "You may expose Kourier via NodePort/port-forward as needed."
else
  echo "Installing Istio minimal profile ..."
  kubectl apply -f https://istio.io/latest/docs/setup/getting-started/
  kubectl apply -f "https://github.com/knative/net-istio/releases/download/knative-v${KN_VERSION}/net-istio.yaml"
fi

# === Domain (magic DNS) ===
kubectl apply -f - <<'YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-domain
  namespace: knative-serving
data:
  127.0.0.1.sslip.io: ""
YAML

# === Wait for readiness ===
echo "Waiting for Knative core components..."
kubectl wait --timeout=300s --for=condition=Available deploy --all -n knative-serving
if [ "${USE_KOURIER}" = "1" ]; then
  kubectl wait --timeout=300s --for=condition=Available deploy --all -n kourier-system
fi

echo "✅ Knative bootstrap complete."
echo "cluster: ${KIND_CLUSTER_NAME}, knative: v${KN_VERSION}, ingress: $([ "${USE_KOURIER}" = "1" ] && echo Kourier || echo Istio)"
