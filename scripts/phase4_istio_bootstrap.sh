#!/usr/bin/env bash
set -euo pipefail

# Phase 4-1: Istio + Gateway API Bootstrap Script
# Installs Istio with minimal configuration for kind/dev environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo "========================================="
echo "Phase 4-1: Istio + Gateway API Bootstrap"
echo "========================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if kind cluster is running
if ! kubectl cluster-info &> /dev/null; then
    log_error "Kubernetes cluster not accessible. Please ensure kind cluster is running."
    exit 1
fi

log_info "Cluster accessible. Proceeding with Istio installation..."

# 1) Install Istio CLI if not available
if ! command -v istioctl &> /dev/null; then
    log_info "Installing Istio CLI..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.1 sh -
    export PATH="$PWD/istio-1.20.1/bin:$PATH"
    
    # Verify installation
    if ! command -v istioctl &> /dev/null; then
        log_error "Failed to install istioctl"
        exit 1
    fi
    
    log_info "Istio CLI installed successfully"
else
    log_info "Istio CLI already available: $(istioctl version --short --remote=false)"
fi

# 2) Create istio-system namespace
log_info "Creating istio-system namespace..."
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# 3) Install Gateway API CRDs
log_info "Installing Gateway API CRDs..."
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# 4) Install Istio with operator configuration
log_info "Installing Istio with minimal configuration..."
istioctl install -f "${PROJECT_ROOT}/infra/k8s/base/istio/istio-operator.yaml" --skip-confirmation

# 5) Wait for Istio components to be ready
log_info "Waiting for Istio components to be ready..."
kubectl wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=istio-ingressgateway -n istio-system --timeout=300s

# 6) Apply Gateway and HTTPRoute
log_info "Applying Gateway API resources..."
kubectl apply -f "${PROJECT_ROOT}/infra/k8s/base/istio/gateway.yaml"
kubectl apply -f "${PROJECT_ROOT}/infra/k8s/base/istio/httproute-hello.yaml"

# 7) Enable sidecar injection for hyper-swarm namespace
log_info "Enabling sidecar injection for hyper-swarm namespace..."
kubectl label namespace hyper-swarm istio-injection=enabled --overwrite

# 8) Restart hello service to get sidecar
log_info "Restarting hello service to inject sidecar..."
kubectl rollout restart ksvc hello -n hyper-swarm || log_warn "Failed to restart hello ksvc (may not exist yet)"

# 9) Show status
echo ""
echo "========================================="
echo "Istio Bootstrap Complete"
echo "========================================="

log_info "Istio components:"
kubectl get pods -n istio-system

echo ""
log_info "Gateway API resources:"
kubectl get gateway -n istio-system
kubectl get httproute -n hyper-swarm

echo ""
log_info "Ingress Gateway service:"
kubectl get svc istio-ingressgateway -n istio-system

echo ""
log_info "To test the setup:"
echo "  # Get NodePort:"
echo "  kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.spec.ports[?(@.name==\"http2\")].nodePort}'"
echo ""
echo "  # Test hello endpoint (once hello service is running):"
echo "  curl -H \"Host: hello.hyper-swarm.svc.cluster.local\" http://localhost:\$NODEPORT/hello"

log_info "Phase 4-1 Istio bootstrap completed successfully!"