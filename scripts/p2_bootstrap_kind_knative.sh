#!/usr/bin/env bash
set -euo pipefail

KIND_NAME="${KIND_NAME:-kind}"
KIND_CFG="${KIND_CFG:-infra/kind-dev/kind-cluster.yaml}"
KN_VERSION="${KN_VERSION:-1.18.0}"
KOURIER_VERSION="${KOURIER_VERSION:-1.18.0}"

SERVING_BASE="https://github.com/knative/serving/releases/download/knative-v${KN_VERSION}"
KOURIER_BASE="https://github.com/knative/net-kourier/releases/download/knative-v${KOURIER_VERSION}"

REPORTS_DIR="reports"
DATESTR="$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="${REPORTS_DIR}/p2_1_bootstrap_${DATESTR}.md"

mkdir -p "$REPORTS_DIR"

log() { printf "\033[1;32m[+]\033[0m %s\n" "$*"; }

# kind cluster (idempotent)
if kind get clusters | grep -qx "${KIND_NAME}"; then
  log "kind cluster '${KIND_NAME}' already exists."
else
  log "creating kind cluster '${KIND_NAME}' ..."
  kind create cluster --name "${KIND_NAME}" --config "${KIND_CFG}"
fi

kubectl config use-context "kind-${KIND_NAME}" >/dev/null 2>&1 || true

# Knative Serving (CRDs + Core)
log "installing Knative Serving v${KN_VERSION} ..."
kubectl apply -f "${SERVING_BASE}/serving-crds.yaml"
kubectl apply -f "${SERVING_BASE}/serving-core.yaml"

# net-kourier
log "installing net-kourier v${KOURIER_VERSION} ..."
kubectl apply -f "${KOURIER_BASE}/kourier.yaml"

# ingress.class = kourier
log "configuring ingress.class=kourier ..."
kubectl patch configmap/config-network -n knative-serving \
  --type merge -p '{"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}}'

# config-domain = 127.0.0.1.sslip.io
log "configuring config-domain -> 127.0.0.1.sslip.io ..."
kubectl patch configmap/config-domain -n knative-serving \
  --type merge -p '{"data":{"127.0.0.1.sslip.io":""}}'

# Wait
log "waiting for knative-serving deployments ..."
for deploy in $(kubectl -n knative-serving get deploy -o name); do
  kubectl -n knative-serving rollout status $deploy --timeout=5m
done
log "waiting for kourier-system deployments ..."
for deploy in $(kubectl -n kourier-system get deploy -o name); do
  kubectl -n kourier-system rollout status $deploy --timeout=5m
done

# Evidence
{
  echo "# P2-1 Bootstrap Evidence (${DATESTR})"
  echo
  echo "## Versions"
  echo '```'
  kubectl version --short || true
  echo
  echo "Knative Serving v${KN_VERSION}"
  echo "net-kourier v${KOURIER_VERSION}"
  echo '```'
  echo
  echo "## knative-serving deployments"
  echo '```'
  kubectl -n knative-serving get deploy -o wide
  echo '```'
  echo
  echo "## kourier-system deployments & services"
  echo '```'
  kubectl -n kourier-system get deploy,svc -o wide
  echo '```'
  echo
  echo "## config-domain"
  echo '```'
  kubectl -n knative-serving get cm config-domain -o yaml
  echo '```'
} > "${REPORT_FILE}"

log "DONE. Evidence saved to: ${REPORT_FILE}"
