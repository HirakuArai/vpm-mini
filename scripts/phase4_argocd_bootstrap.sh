#!/usr/bin/env bash
set -euo pipefail

# Phase 4-2: Argo CD GitOps Bootstrap Script
# Installs Argo CD with minimal configuration for kind/dev environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
ARGO_VERSION="${ARGO_VERSION:-v2.9.7}"

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
echo "Phase 4-2: Argo CD GitOps Bootstrap"
echo "========================================="
echo "Argo CD Version: ${ARGO_VERSION}"
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

log_info "Cluster accessible. Proceeding with Argo CD installation..."

# 1) Create argocd namespace
log_info "Creating argocd namespace..."
kubectl apply -f "${PROJECT_ROOT}/infra/k8s/base/argocd/namespace.yaml"

# 2) Apply official Argo CD manifests (fixed version)
log_info "Installing Argo CD components (version: ${ARGO_VERSION})..."
kubectl -n argocd apply -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGO_VERSION}/manifests/install.yaml"

# 3) Patch argocd-server for insecure mode (dev environment)
log_info "Configuring argocd-server for insecure mode (dev environment)..."
kubectl -n argocd patch deployment argocd-server \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"argocd-server","command":["argocd-server","--insecure"]}]}}}}' || \
  log_warn "Failed to patch argocd-server for insecure mode (might already be configured)"

# 4) Wait for core components to be ready
log_info "Waiting for Argo CD core components to be ready..."

log_info "  Waiting for argocd-server..."
kubectl -n argocd rollout status deploy/argocd-server --timeout=300s

log_info "  Waiting for argocd-repo-server..."
kubectl -n argocd rollout status deploy/argocd-repo-server --timeout=300s

log_info "  Waiting for argocd-application-controller..."
kubectl -n argocd rollout status deploy/argocd-application-controller --timeout=300s

# 5) Optional: Wait for other components
log_info "  Waiting for additional components..."
kubectl -n argocd rollout status deploy/argocd-dex-server --timeout=180s || log_warn "dex-server not ready (optional)"
kubectl -n argocd rollout status deploy/argocd-redis --timeout=180s || log_warn "redis not ready (optional)"

# 6) Show status
echo ""
echo "========================================="
echo "Argo CD Bootstrap Complete"
echo "========================================="

log_info "Argo CD pods:"
kubectl get pods -n argocd

echo ""
log_info "Argo CD services:"
kubectl get svc -n argocd

echo ""
log_info "To access Argo CD UI (optional):"
echo "  # Port-forward to access UI:"
echo "  kubectl -n argocd port-forward svc/argocd-server 8080:80"
echo "  # Then open: http://localhost:8080"
echo ""
echo "  # Get initial admin password:"
echo "  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"

echo ""
log_info "Next steps:"
echo "  1. Apply root Application: kubectl apply -f infra/gitops/root-app.yaml"
echo "  2. Verify GitOps sync: bash scripts/phase4_argocd_verify.sh"

log_info "[OK] Argo CD bootstrap complete!"