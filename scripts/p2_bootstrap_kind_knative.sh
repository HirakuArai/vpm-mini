#!/usr/bin/env bash
set -euo pipefail
CLUSTER="${CLUSTER:-vpm-mini}"
KIND_NODE_IMAGE="${KIND_NODE_IMAGE:-kindest/node:v1.29.2}"
KN_VERSION="${KN_VERSION:-knative-v1.18.0}"
KOURIER_VERSION="${KOURIER_VERSION:-knative-v1.18.0}"
DOMAIN="${DOMAIN:-127.0.0.1.nip.io}"
REPORT_DIR="${REPORT_DIR:-reports}"
mkdir -p "${REPORT_DIR}"
ts(){ date +"%Y-%m-%dT%H%M%S%z"; }
log(){ echo "[$(ts)] $*"; }

log "== kind cluster =="
if ! kind get clusters | grep -qx "${CLUSTER}"; then
  log "creating kind cluster ${CLUSTER}"
  kind create cluster --name "${CLUSTER}" --image "${KIND_NODE_IMAGE}"
else
  log "kind cluster ${CLUSTER} already exists"
fi

export KUBECONFIG="${HOME}/.kube/config"

log "== Knative Serving ${KN_VERSION} =="
if ! kubectl get ns knative-serving >/dev/null 2>&1; then
  kubectl apply -f "https://github.com/knative/serving/releases/download/${KN_VERSION}/serving-crds.yaml"
  kubectl apply -f "https://github.com/knative/serving/releases/download/${KN_VERSION}/serving-core.yaml"
fi

log "== Kourier ${KOURIER_VERSION} =="
kubectl apply -f "https://github.com/knative/net-kourier/releases/download/${KOURIER_VERSION}/kourier.yaml"

log "== Configure ingress-class/domain =="
kubectl patch configmap/config-network -n knative-serving --type merge -p '{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'
kubectl apply -n knative-serving -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata: {name: config-domain, namespace: knative-serving}
data: {${DOMAIN}: ""}
EOF

log "== Wait for control-plane =="
kubectl wait --for=condition=Available deploy --all -n knative-serving --timeout=300s
kubectl wait --for=condition=Available deploy --all -n kourier-system  --timeout=300s

OUT="${REPORT_DIR}/p2_boot_$(date +%Y%m%dT%H%M%S).md"
{
  echo "# P2-1 bootstrap ($(ts))"
  echo "## knative-serving";  kubectl get pods -n knative-serving -o wide
  echo; echo "## kourier-system"; kubectl get pods -n kourier-system -o wide
  echo; echo "## services";       kubectl get svc  -n kourier-system -o wide
} | tee "${OUT}"
log "done. report=${OUT}"
