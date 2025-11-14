#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="vpm-mini-kind"
KIND_CONFIG="infra/kind-dev/kind-cluster.yaml"
HELLO_MANIFEST="infra/k8s/overlays/dev/hello-ksvc.yaml"
HELLO_NS="default"

log(){
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

require_binary(){
  if ! command -v "$1" >/dev/null 2>&1; then
    log "ERROR: required command '$1' not found. Install it first." >&2
    exit 1
  fi
}

cluster_exists(){
  kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"
}

create_cluster(){
  log "Creating kind cluster '$CLUSTER_NAME' via $KIND_CONFIG"
  kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
}

ensure_cluster(){
  if cluster_exists; then
    log "Reusing existing kind cluster '$CLUSTER_NAME'"
  else
    create_cluster
  fi
  kubectl config use-context "kind-$CLUSTER_NAME"
}

deploy_knative(){
  log "TODO: install Knative Serving v1.18 (CRDs + core)"
  # TODO: Knative CRD インストール
  # Example placeholder:
  # kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.18.0/serving-crds.yaml
  log "TODO: install Knative core"
  # TODO: Knative core インストール
  log "TODO: install kourier as ingress"
  # TODO: kourier インストール
}

apply_hello(){
  if [ ! -f "$HELLO_MANIFEST" ]; then
    log "ERROR: manifest $HELLO_MANIFEST not found" >&2
    exit 1
  fi
  log "Applying hello-ksvc manifest"
  kubectl apply -f "$HELLO_MANIFEST"
  log "Waiting for ksvc/hello Ready"
  kubectl -n "$HELLO_NS" wait ksvc hello --for=condition=Ready --timeout=300s
  log "Dumping ksvc hello summary"
  kubectl -n "$HELLO_NS" get ksvc hello -oyaml | sed -n '1,80p'
}

main(){
  require_binary kind
  require_binary kubectl
  ensure_cluster
  deploy_knative
  apply_hello
  log "Bootstrap complete"
}

main "$@"
