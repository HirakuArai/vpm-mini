#!/usr/bin/env bash
#
# Phase 5-4: Multi-Cluster GitOps Bootstrap
# Register cluster-a and cluster-b to ArgoCD with ApplicationSet deployment
#

set -euo pipefail

# Configuration with defaults for kind clusters
A_CTX=${A_CTX:-kind-cluster-a}
B_CTX=${B_CTX:-kind-cluster-b}
ARGOCD_SERVER=${ARGOCD_SERVER:-localhost:31390}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}"/..)" && pwd)"

# Colors for output
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_phase() {
    echo -e "${BLUE}[PHASE]${NC} $*"
}

check_prerequisites() {
    log_phase "Checking prerequisites..."
    
    # Check if kubectl contexts exist
    if ! kubectl config get-contexts "$A_CTX" >/dev/null 2>&1; then
        log_error "kubectl context '$A_CTX' not found"
        log_error "Please create cluster-a or set A_CTX environment variable"
        exit 1
    fi
    
    if ! kubectl config get-contexts "$B_CTX" >/dev/null 2>&1; then
        log_error "kubectl context '$B_CTX' not found"
        log_error "Please create cluster-b or set B_CTX environment variable"
        exit 1
    fi
    
    # Check if argocd CLI is available
    if ! command -v argocd >/dev/null 2>&1; then
        log_error "argocd CLI not found"
        log_error "Please install argocd CLI or use kubectl to manage cluster secrets directly"
        exit 1
    fi
    
    # Check ArgoCD connection
    if ! argocd cluster list >/dev/null 2>&1; then
        log_warn "ArgoCD CLI not authenticated, attempting to login..."
        log_info "Please ensure ArgoCD is accessible and you are authenticated"
        log_info "You can authenticate with: argocd login $ARGOCD_SERVER"
    fi
    
    log_info "✅ Prerequisites check completed"
}

verify_cluster_connectivity() {
    local ctx="$1"
    local cluster_name="$2"
    
    log_info "Verifying connectivity to $cluster_name ($ctx)..."
    
    if ! kubectl --context "$ctx" cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to cluster $cluster_name ($ctx)"
        return 1
    fi
    
    # Check if required namespaces exist or can be created
    for ns in hyper-swarm istio-system monitoring; do
        if ! kubectl --context "$ctx" get namespace "$ns" >/dev/null 2>&1; then
            log_info "Creating namespace $ns in $cluster_name..."
            kubectl --context "$ctx" create namespace "$ns" || log_warn "Failed to create namespace $ns"
        fi
    done
    
    log_info "✅ Cluster connectivity verified for $cluster_name"
}

register_cluster() {
    local ctx="$1"
    local cluster_name="$2"
    local region="$3"
    
    log_phase "Registering cluster $cluster_name ($ctx)..."
    
    # Check if cluster is already registered
    if argocd cluster list | grep -q "$cluster_name"; then
        log_warn "Cluster $cluster_name already registered, skipping registration"
    else
        log_info "Adding cluster $cluster_name to ArgoCD..."
        if argocd cluster add "$ctx" --name "$cluster_name" --yes; then
            log_info "✅ Cluster $cluster_name registered successfully"
        else
            log_error "Failed to register cluster $cluster_name"
            return 1
        fi
    fi
    
    # Add region label to cluster secret
    log_info "Adding region label to cluster secret..."
    
    # Find the cluster secret
    local secret_name
    secret_name=$(kubectl -n argocd get secrets -l argocd.argoproj.io/secret-type=cluster -o name | \
                 xargs -I {} kubectl -n argocd get {} -o jsonpath='{.metadata.name}:{.data.name}' | \
                 grep ":$(echo -n "$cluster_name" | base64 -w 0)" | cut -d: -f1 || true)
    
    if [[ -n "$secret_name" ]]; then
        kubectl -n argocd label secret "$secret_name" region="$region" --overwrite
        log_info "✅ Added region=$region label to cluster secret"
    else
        log_warn "Could not find cluster secret for $cluster_name to add region label"
    fi
}

configure_cluster_networking() {
    local ctx="$1"
    local cluster_name="$2"
    local nodeport="$3"
    
    log_phase "Configuring networking for $cluster_name..."
    
    # Check if istio-ingressgateway exists
    if ! kubectl --context "$ctx" -n istio-system get svc istio-ingressgateway >/dev/null 2>&1; then
        log_warn "istio-ingressgateway not found in $cluster_name, skipping NodePort configuration"
        return 0
    fi
    
    log_info "Setting NodePort $nodeport for $cluster_name istio-ingressgateway..."
    
    # Update the NodePort for istio-ingressgateway
    kubectl --context "$ctx" -n istio-system patch svc istio-ingressgateway --type='json' -p="[
        {\"op\": \"replace\", \"path\": \"/spec/ports/0/nodePort\", \"value\": $nodeport}
    ]" || log_warn "Failed to patch istio-ingressgateway NodePort"
    
    # Verify the change
    local actual_nodeport
    actual_nodeport=$(kubectl --context "$ctx" -n istio-system get svc istio-ingressgateway -o jsonpath='{.spec.ports[0].nodePort}')
    
    if [[ "$actual_nodeport" == "$nodeport" ]]; then
        log_info "✅ NodePort configured successfully: $nodeport"
    else
        log_warn "NodePort configuration may not have taken effect (expected: $nodeport, actual: $actual_nodeport)"
    fi
}

deploy_applicationset() {
    log_phase "Deploying ApplicationSet..."
    
    # Ensure the appset directory exists
    if [[ ! -d "$PROJECT_ROOT/infra/gitops/appset" ]]; then
        log_error "ApplicationSet directory not found: $PROJECT_ROOT/infra/gitops/appset"
        exit 1
    fi
    
    # Apply ApplicationSet using kustomize
    log_info "Applying ApplicationSet resources..."
    kubectl apply -k "$PROJECT_ROOT/infra/gitops/appset/"
    
    if [[ $? -eq 0 ]]; then
        log_info "✅ ApplicationSet deployed successfully"
    else
        log_error "Failed to deploy ApplicationSet"
        return 1
    fi
    
    # Wait for ApplicationSet to process
    log_info "Waiting for ApplicationSet to generate Applications..."
    sleep 10
    
    # Verify Applications were created
    local app_count
    app_count=$(kubectl -n argocd get applications -l app.kubernetes.io/component=root-app -o name | wc -l)
    
    log_info "Generated Applications: $app_count"
    if [[ "$app_count" -gt 0 ]]; then
        kubectl -n argocd get applications -l app.kubernetes.io/component=root-app
    fi
}

verify_bootstrap() {
    log_phase "Verifying bootstrap results..."
    
    # Check registered clusters
    log_info "Registered clusters:"
    argocd cluster list || kubectl -n argocd get secrets -l argocd.argoproj.io/secret-type=cluster
    
    # Check generated Applications
    log_info "Generated Applications:"
    kubectl -n argocd get applications -l app.kubernetes.io/component=root-app -o wide
    
    # Check ApplicationSet status
    log_info "ApplicationSet status:"
    kubectl -n argocd get applicationsets -o wide
}

main() {
    echo "=============================================="
    echo "Phase 5-4: Multi-Cluster GitOps Bootstrap"
    echo "=============================================="
    echo
    echo "Configuration:"
    echo "  Cluster A Context: $A_CTX (NodePort: 31380)"  
    echo "  Cluster B Context: $B_CTX (NodePort: 32380)"
    echo "  ArgoCD Server: $ARGOCD_SERVER"
    echo
    
    # Check prerequisites
    check_prerequisites
    echo
    
    # Verify cluster connectivity
    verify_cluster_connectivity "$A_CTX" "cluster-a"
    verify_cluster_connectivity "$B_CTX" "cluster-b"
    echo
    
    # Register clusters with region labels
    register_cluster "$A_CTX" "cluster-a" "a"
    register_cluster "$B_CTX" "cluster-b" "b"
    echo
    
    # Configure cluster-specific networking
    configure_cluster_networking "$A_CTX" "cluster-a" 31380
    configure_cluster_networking "$B_CTX" "cluster-b" 32380
    echo
    
    # Deploy ApplicationSet
    deploy_applicationset
    echo
    
    # Verify final state
    verify_bootstrap
    echo
    
    log_phase "Bootstrap completed successfully!"
    log_info "ApplicationSet will automatically generate and sync Applications to both clusters"
    log_info "Run 'bash scripts/phase5_appset_verify.sh' to verify the deployment status"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  -h, --help              Show this help"
        echo "  A_CTX=<context>         Cluster A kubectl context (default: kind-cluster-a)"
        echo "  B_CTX=<context>         Cluster B kubectl context (default: kind-cluster-b)"
        echo "  ARGOCD_SERVER=<server>  ArgoCD server address (default: localhost:31390)"
        echo
        echo "Example:"
        echo "  A_CTX=prod-east B_CTX=prod-west $0"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac