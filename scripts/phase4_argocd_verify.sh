#!/usr/bin/env bash
set -euo pipefail

# Phase 4-2: Argo CD GitOps Verification Script
# Verifies root-app sync status and gitops-check ConfigMap presence

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
echo "Phase 4-2: Argo CD GitOps Verification"
echo "========================================="

# Create reports directory
mkdir -p "${PROJECT_ROOT}/reports"

# Initialize results
SYNCED=false
HEALTHY=false
CONFIGMAP_PRESENT=false

# 1) Check if Argo CD components are running
log_info "Checking Argo CD components..."

ARGOCD_READY=true
for component in argocd-server argocd-repo-server argocd-application-controller; do
    if kubectl -n argocd get deploy "$component" >/dev/null 2>&1; then
        READY_REPLICAS=$(kubectl -n argocd get deploy "$component" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        DESIRED_REPLICAS=$(kubectl -n argocd get deploy "$component" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
        
        if [[ "$READY_REPLICAS" == "$DESIRED_REPLICAS" && "$READY_REPLICAS" != "0" ]]; then
            log_info "  ✅ $component: Ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
        else
            log_warn "  ⚠️  $component: Not ready ($READY_REPLICAS/$DESIRED_REPLICAS)"
            ARGOCD_READY=false
        fi
    else
        log_error "  ❌ $component: Not found"
        ARGOCD_READY=false
    fi
done

if [[ "$ARGOCD_READY" != "true" ]]; then
    log_warn "Argo CD components not fully ready, but proceeding with verification..."
fi

# 2) Check root-app Application status
log_info "Checking root-app Application status..."

if kubectl -n argocd get application root-app >/dev/null 2>&1; then
    log_info "root-app Application found"
    
    # Get Application JSON
    APP_JSON=$(kubectl -n argocd get application root-app -o json 2>/dev/null || echo '{}')
    
    # Check sync status
    SYNC_STATUS=$(echo "$APP_JSON" | jq -r '.status.sync.status // "Unknown"' 2>/dev/null || echo "Unknown")
    log_info "  Sync Status: $SYNC_STATUS"
    
    if [[ "$SYNC_STATUS" == "Synced" ]]; then
        SYNCED=true
        log_info "  ✅ Application is Synced"
    else
        log_warn "  ⚠️  Application sync status: $SYNC_STATUS (expected: Synced)"
    fi
    
    # Check health status
    HEALTH_STATUS=$(echo "$APP_JSON" | jq -r '.status.health.status // "Unknown"' 2>/dev/null || echo "Unknown")
    log_info "  Health Status: $HEALTH_STATUS"
    
    if [[ "$HEALTH_STATUS" == "Healthy" ]]; then
        HEALTHY=true
        log_info "  ✅ Application is Healthy"
    else
        log_warn "  ⚠️  Application health status: $HEALTH_STATUS (expected: Healthy)"
    fi
    
    # Show resources if available
    RESOURCES=$(echo "$APP_JSON" | jq -r '.status.resources // []' 2>/dev/null || echo "[]")
    RESOURCE_COUNT=$(echo "$RESOURCES" | jq '. | length' 2>/dev/null || echo "0")
    log_info "  Managed Resources: $RESOURCE_COUNT"
    
else
    log_error "root-app Application not found in argocd namespace"
    log_error "Please ensure root-app is applied: kubectl apply -f infra/gitops/root-app.yaml"
fi

# 3) Check gitops-check ConfigMap presence
log_info "Checking gitops-check ConfigMap..."

if kubectl -n hyper-swarm get configmap gitops-check >/dev/null 2>&1; then
    CONFIGMAP_PRESENT=true
    log_info "  ✅ gitops-check ConfigMap found in hyper-swarm namespace"
    
    # Show ConfigMap details
    CM_MESSAGE=$(kubectl -n hyper-swarm get configmap gitops-check -o jsonpath='{.data.message}' 2>/dev/null || echo "N/A")
    log_info "  Message: $CM_MESSAGE"
else
    log_warn "  ⚠️  gitops-check ConfigMap not found in hyper-swarm namespace"
    log_warn "  This may indicate the root-app has not synced successfully"
fi

# 4) Generate verification results
OUT_JSON="${PROJECT_ROOT}/reports/phase4_argocd_verify.json"

log_info "Generating verification results..."

# Create comprehensive JSON result
cat > "$OUT_JSON" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "commit": "$(git rev-parse --short HEAD)",
  "branch": "$(git branch --show-current)",
  "argocd_ready": $ARGOCD_READY,
  "root_app": {
    "synced": $SYNCED,
    "healthy": $HEALTHY,
    "sync_status": "$SYNC_STATUS",
    "health_status": "$HEALTH_STATUS"
  },
  "gitops_resources": {
    "configmap_present": $CONFIGMAP_PRESENT
  },
  "overall_status": {
    "synced": $SYNCED,
    "healthy": $HEALTHY,
    "configmap_present": $CONFIGMAP_PRESENT,
    "all_ok": $(if [[ "$SYNCED" == "true" && "$HEALTHY" == "true" && "$CONFIGMAP_PRESENT" == "true" ]]; then echo "true"; else echo "false"; fi)
  }
}
EOF

# Pretty print results
log_info "Verification results saved to: $OUT_JSON"
jq '.' "$OUT_JSON"

# 5) Generate snapshot report
log_info "Generating snapshot report..."

DATE_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT=$(git rev-parse --short HEAD)
VERIFY_JSON_REL="reports/phase4_argocd_verify.json"

# Process template if it exists
TEMPLATE_FILE="${PROJECT_ROOT}/reports/templates/phase4_argocd_report.md.tmpl"
SNAPSHOT_FILE="${PROJECT_ROOT}/reports/snap_phase4-2-argocd-ready.md"

if [[ -f "$TEMPLATE_FILE" ]]; then
    sed -e "s|{{DATE}}|$DATE_ISO|g" \
        -e "s|{{COMMIT}}|$COMMIT|g" \
        -e "s|{{VERIFY_JSON}}|$VERIFY_JSON_REL|g" \
        -e "s|{{SYNCED}}|$SYNCED|g" \
        -e "s|{{HEALTHY}}|$HEALTHY|g" \
        -e "s|{{CONFIGMAP_PRESENT}}|$CONFIGMAP_PRESENT|g" \
        -e "s|{{SYNC_STATUS}}|$SYNC_STATUS|g" \
        -e "s|{{HEALTH_STATUS}}|$HEALTH_STATUS|g" \
        "$TEMPLATE_FILE" > "$SNAPSHOT_FILE"
    
    log_info "Snapshot report generated: $SNAPSHOT_FILE"
else
    log_warn "Template file not found: $TEMPLATE_FILE"
fi

# 6) Summary and exit
echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="

ALL_OK=$(jq -r '.overall_status.all_ok' "$OUT_JSON")

if [[ "$ALL_OK" == "true" ]]; then
    log_info "✅ Phase 4-2 Argo CD GitOps verification PASSED"
    log_info "   - root-app: Synced & Healthy"
    log_info "   - gitops-check ConfigMap: Present"
    log_info "   - GitOps foundation successfully established"
    exit 0
else
    log_error "❌ Phase 4-2 Argo CD GitOps verification FAILED"
    [[ "$SYNCED" != "true" ]] && log_error "   - root-app sync status: $SYNC_STATUS (expected: Synced)"
    [[ "$HEALTHY" != "true" ]] && log_error "   - root-app health status: $HEALTH_STATUS (expected: Healthy)"
    [[ "$CONFIGMAP_PRESENT" != "true" ]] && log_error "   - gitops-check ConfigMap not found"
    echo ""
    log_warn "Troubleshooting steps:"
    log_warn "   1. Check root-app status: kubectl -n argocd get app root-app -o yaml"
    log_warn "   2. Check Argo CD logs: kubectl -n argocd logs deploy/argocd-application-controller"
    log_warn "   3. Verify repository access and path: infra/gitops/apps"
    exit 1
fi