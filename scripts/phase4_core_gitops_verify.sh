#!/usr/bin/env bash
set -euo pipefail

# Phase 4-4: Core Infrastructure GitOps Migration Verification Script
# Verifies Gateway and NetworkPolicy resources are tracked by Argo CD and external access maintained

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
URL="${URL:-http://localhost:31380/hello}"
REQUEST_COUNT="${N:-30}"
TIMEOUT=2

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
echo "Phase 4-4: Core GitOps Migration Verification"
echo "========================================="
echo "URL: $URL"
echo "Requests: $REQUEST_COUNT"
echo "========================================="

# Create reports directory
mkdir -p "${PROJECT_ROOT}/reports"

# Initialize results
SYNCED=false
HEALTHY=false
GATEWAY_TRACKED=false
NETPOL_TRACKED=false
SUCCESS_RATE=0
P50_MS=0

# 1) Get Argo CD Application status
log_info "Checking root-app Application status..."

if ! kubectl -n argocd get application root-app >/dev/null 2>&1; then
    log_error "root-app Application not found"
    exit 1
fi

APP_JSON=$(kubectl -n argocd get application root-app -o json 2>/dev/null || echo '{}')

# Check sync status
SYNC_STATUS=$(echo "$APP_JSON" | jq -r '.status.sync.status // "Unknown"' 2>/dev/null || echo "Unknown")
if [[ "$SYNC_STATUS" == "Synced" ]]; then
    SYNCED=true
    log_info "✅ root-app is Synced"
else
    log_warn "⚠️  root-app sync status: $SYNC_STATUS"
fi

# Check health status
HEALTH_STATUS=$(echo "$APP_JSON" | jq -r '.status.health.status // "Unknown"' 2>/dev/null || echo "Unknown")
if [[ "$HEALTH_STATUS" == "Healthy" ]]; then
    HEALTHY=true
    log_info "✅ root-app is Healthy"
else
    log_warn "⚠️  root-app health status: $HEALTH_STATUS"
fi

# 2) Check if Argo CD is tracking Gateway resources
log_info "Checking Gateway resource tracking..."

GATEWAY_FOUND=$(echo "$APP_JSON" | jq -r '.status.resources[]? | select(.kind=="Gateway") | .name' 2>/dev/null | grep -q "^vpm-mini-gateway$" && echo true || echo false)

if [[ "$GATEWAY_FOUND" == "true" ]]; then
    GATEWAY_TRACKED=true
    log_info "✅ Gateway 'vpm-mini-gateway' tracked by Argo CD"
else
    log_warn "⚠️  Gateway 'vpm-mini-gateway' not tracked by Argo CD"
fi

# 3) Check if Argo CD is tracking NetworkPolicy resources
log_info "Checking NetworkPolicy resource tracking..."

NETPOL_COUNT=$(echo "$APP_JSON" | jq -r '[.status.resources[]? | select(.kind=="NetworkPolicy")] | length' 2>/dev/null || echo "0")

log_info "NetworkPolicies tracked by Argo CD: $NETPOL_COUNT"

if [[ "$NETPOL_COUNT" -ge 2 ]]; then
    NETPOL_TRACKED=true
    log_info "✅ NetworkPolicies tracked by Argo CD (count: $NETPOL_COUNT ≥ 2)"
    
    # List the NetworkPolicies for verification
    echo "$APP_JSON" | jq -r '.status.resources[]? | select(.kind=="NetworkPolicy") | "  - \(.name)"' 2>/dev/null || true
else
    log_warn "⚠️  Insufficient NetworkPolicies tracked (count: $NETPOL_COUNT, expected: ≥ 2)"
fi

# 4) Show all tracked resources for debugging
log_info "All resources tracked by root-app:"
echo "$APP_JSON" | jq -r '.status.resources[]? | "  \(.kind) \(.name) (\(.namespace // "default"))"' 2>/dev/null || log_warn "Unable to list resources"

# 5) External reachability test with detailed metrics
log_info "Testing external reachability: $URL"

SUCCESS_COUNT=0
LATENCIES=()

for i in $(seq 1 "$REQUEST_COUNT"); do
    START_TIME=$(date +%s%3N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$URL" 2>/dev/null || echo "000")
    END_TIME=$(date +%s%3N)
    
    LATENCY_MS=$((END_TIME - START_TIME))
    LATENCIES+=("$LATENCY_MS")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
    
    sleep 0.1
done

# Calculate success rate and p50 latency
SUCCESS_RATE=$(python3 -c "print(round($SUCCESS_COUNT / $REQUEST_COUNT, 3))")

if [[ ${#LATENCIES[@]} -gt 0 ]]; then
    P50_MS=$(python3 - <<EOF
import statistics
latencies = [${LATENCIES[*]}]
print(int(statistics.median(latencies)))
EOF
)
else
    P50_MS=0
fi

log_info "External access results:"
log_info "  Success rate: $SUCCESS_RATE ($SUCCESS_COUNT/$REQUEST_COUNT)"
log_info "  P50 latency: ${P50_MS}ms"

# Check if success rate meets target
REACHABLE=false
if (( $(echo "$SUCCESS_RATE >= 0.95" | bc -l) )); then
    REACHABLE=true
    log_info "✅ Success rate ≥ 95%: $SUCCESS_RATE"
else
    log_warn "⚠️  Success rate below 95%: $SUCCESS_RATE"
fi

# 6) Generate verification results
OUT_JSON="${PROJECT_ROOT}/reports/phase4_core_gitops_verify.json"

log_info "Generating verification results..."

cat > "$OUT_JSON" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "commit": "$(git rev-parse --short HEAD)",
  "branch": "$(git branch --show-current)",
  "root_app": {
    "synced": $SYNCED,
    "healthy": $HEALTHY,
    "sync_status": "$SYNC_STATUS",
    "health_status": "$HEALTH_STATUS"
  },
  "resource_tracking": {
    "gateway_tracked": $GATEWAY_TRACKED,
    "netpol_tracked": $NETPOL_TRACKED,
    "netpol_count": $NETPOL_COUNT
  },
  "external_access": {
    "reachable": $REACHABLE,
    "success_rate": $SUCCESS_RATE,
    "p50_ms": $P50_MS,
    "successful_requests": $SUCCESS_COUNT,
    "total_requests": $REQUEST_COUNT
  },
  "overall_status": {
    "synced": $SYNCED,
    "healthy": $HEALTHY,
    "gateway_tracked": $GATEWAY_TRACKED,
    "netpol_tracked": $NETPOL_TRACKED,
    "reachable": $REACHABLE,
    "success_rate": $SUCCESS_RATE,
    "p50_ms": $P50_MS,
    "all_ok": $(if [[ "$SYNCED" == "true" && "$HEALTHY" == "true" && "$GATEWAY_TRACKED" == "true" && "$NETPOL_TRACKED" == "true" && "$REACHABLE" == "true" ]]; then echo "true"; else echo "false"; fi)
  }
}
EOF

# Pretty print results
log_info "Core GitOps verification results saved to: $OUT_JSON"
jq '.' "$OUT_JSON"

# 7) Generate snapshot report
log_info "Generating snapshot report..."

DATE_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT=$(git rev-parse --short HEAD)
VERIFY_JSON_REL="reports/phase4_core_gitops_verify.json"

# Process template if it exists
TEMPLATE_FILE="${PROJECT_ROOT}/reports/templates/phase4_core_gitops_report.md.tmpl"
SNAPSHOT_FILE="${PROJECT_ROOT}/reports/snap_phase4-4-core-gitops.md"

if [[ -f "$TEMPLATE_FILE" ]]; then
    sed -e "s|{{DATE}}|$DATE_ISO|g" \
        -e "s|{{COMMIT}}|$COMMIT|g" \
        -e "s|{{VERIFY_JSON}}|$VERIFY_JSON_REL|g" \
        -e "s|{{SYNCED}}|$SYNCED|g" \
        -e "s|{{HEALTHY}}|$HEALTHY|g" \
        -e "s|{{GATEWAY_TRACKED}}|$GATEWAY_TRACKED|g" \
        -e "s|{{NETPOL_TRACKED}}|$NETPOL_TRACKED|g" \
        -e "s|{{NETPOL_COUNT}}|$NETPOL_COUNT|g" \
        -e "s|{{SUCCESS_RATE}}|$SUCCESS_RATE|g" \
        -e "s|{{P50_MS}}|$P50_MS|g" \
        -e "s|{{SUCCESS_COUNT}}|$SUCCESS_COUNT|g" \
        -e "s|{{REQUEST_COUNT}}|$REQUEST_COUNT|g" \
        "$TEMPLATE_FILE" > "$SNAPSHOT_FILE"
    
    log_info "Snapshot report generated: $SNAPSHOT_FILE"
else
    log_warn "Template file not found: $TEMPLATE_FILE"
fi

# 8) Summary and exit
echo ""
echo "========================================="
echo "Core GitOps Migration Verification Summary"
echo "========================================="

ALL_OK=$(jq -r '.overall_status.all_ok' "$OUT_JSON")

if [[ "$ALL_OK" == "true" ]]; then
    log_info "✅ Phase 4-4 Core GitOps migration verification PASSED"
    log_info "   - root-app: Synced & Healthy"
    log_info "   - Gateway 'vpm-mini-gateway': Tracked by Argo CD"
    log_info "   - NetworkPolicies: $NETPOL_COUNT tracked (≥ 2 required)"
    log_info "   - External access: Success rate $SUCCESS_RATE (≥ 0.95), P50 ${P50_MS}ms"
    log_info "   - Core infrastructure successfully migrated to GitOps"
    echo ""
    log_info "[OK] core gitops verify: success_rate=${SUCCESS_RATE}, p50=${P50_MS}ms"
    exit 0
else
    log_error "❌ Phase 4-4 Core GitOps migration verification FAILED"
    [[ "$SYNCED" != "true" ]] && log_error "   - root-app sync status: $SYNC_STATUS"
    [[ "$HEALTHY" != "true" ]] && log_error "   - root-app health status: $HEALTH_STATUS"
    [[ "$GATEWAY_TRACKED" != "true" ]] && log_error "   - Gateway 'vpm-mini-gateway' not tracked"
    [[ "$NETPOL_TRACKED" != "true" ]] && log_error "   - NetworkPolicies insufficient (count: $NETPOL_COUNT)"
    [[ "$REACHABLE" != "true" ]] && log_error "   - External access failed (success rate: $SUCCESS_RATE)"
    echo ""
    log_warn "Troubleshooting steps:"
    log_warn "   1. Check root-app sync: kubectl -n argocd get app root-app -o yaml"
    log_warn "   2. Verify Gateway exists: kubectl -n istio-system get gateway"
    log_warn "   3. Verify NetworkPolicies: kubectl -n hyper-swarm get networkpolicy"
    log_warn "   4. Check external connectivity: curl -v $URL"
    echo ""
    log_info "[OK] core gitops verify: success_rate=${SUCCESS_RATE}, p50=${P50_MS}ms (with issues)"
    exit 1
fi