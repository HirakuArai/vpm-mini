#!/usr/bin/env bash
set -euo pipefail

# Phase 4-3: Hello Resources Migration Verification Script
# Verifies hello resources are tracked by Argo CD and externally reachable

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
echo "Phase 4-3: Hello Migration Verification"
echo "========================================="
echo "URL: $URL"
echo "Requests: $REQUEST_COUNT"
echo "========================================="

# Create reports directory
mkdir -p "${PROJECT_ROOT}/reports"

# Initialize results
SYNCED=false
HEALTHY=false
KSVC_TRACKED=false
HTTPROUTE_TRACKED=false
REACHABLE=false
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

# 2) Check if Argo CD is tracking hello resources
log_info "Checking Argo CD resource tracking..."

# Check for Knative Service (hello)
# Try multiple possible kinds that Argo CD might report
KSVC_FOUND=$(echo "$APP_JSON" | jq -r '.status.resources[]? | select(.kind=="Service" and (.group=="serving.knative.dev" or .apiVersion | contains("serving.knative.dev"))) | .name' 2>/dev/null | grep -q "^hello$" && echo true || echo false)

if [[ "$KSVC_FOUND" == "true" ]]; then
    KSVC_TRACKED=true
    log_info "✅ Knative Service 'hello' tracked by Argo CD"
else
    # Fallback: check for any Service named hello
    SERVICE_FOUND=$(echo "$APP_JSON" | jq -r '.status.resources[]? | select(.kind=="Service" and .name=="hello") | .name' 2>/dev/null | grep -q "^hello$" && echo true || echo false)
    if [[ "$SERVICE_FOUND" == "true" ]]; then
        KSVC_TRACKED=true
        log_info "✅ Service 'hello' tracked by Argo CD"
    else
        log_warn "⚠️  Knative Service 'hello' not tracked by Argo CD"
    fi
fi

# Check for HTTPRoute (hello-route)
HTTPROUTE_FOUND=$(echo "$APP_JSON" | jq -r '.status.resources[]? | select(.kind=="HTTPRoute") | .name' 2>/dev/null | grep -q "^hello-route$" && echo true || echo false)

if [[ "$HTTPROUTE_FOUND" == "true" ]]; then
    HTTPROUTE_TRACKED=true
    log_info "✅ HTTPRoute 'hello-route' tracked by Argo CD"
else
    log_warn "⚠️  HTTPRoute 'hello-route' not tracked by Argo CD"
fi

# 3) Show all tracked resources for debugging
log_info "All resources tracked by root-app:"
echo "$APP_JSON" | jq -r '.status.resources[]? | "  \(.kind) \(.name) (\(.namespace // "default"))"' 2>/dev/null || log_warn "Unable to list resources"

# 4) External reachability test
log_info "Testing external reachability: $URL"

TEMP_FILE=$(mktemp)
SUCCESS_COUNT=0
LATENCIES=()

for i in $(seq 1 "$REQUEST_COUNT"); do
    START_TIME=$(date +%s%3N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$URL" 2>/dev/null || echo "000")
    END_TIME=$(date +%s%3N)
    
    LATENCY_MS=$((END_TIME - START_TIME))
    echo "$LATENCY_MS" >> "$TEMP_FILE"
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
    
    sleep 0.1
done

# Calculate p50 latency using Python
if [[ $SUCCESS_COUNT -gt 0 ]]; then
    REACHABLE=true
    P50_MS=$(python3 - "$TEMP_FILE" <<'EOF'
import sys, statistics
with open(sys.argv[1]) as f:
    latencies = [int(line.strip()) for line in f if line.strip().isdigit()]
if latencies:
    print(int(statistics.median(latencies)))
else:
    print(0)
EOF
)
    log_info "✅ Hello service reachable: $SUCCESS_COUNT/$REQUEST_COUNT requests successful"
    log_info "✅ P50 latency: ${P50_MS}ms"
else
    log_warn "⚠️  Hello service not reachable: 0/$REQUEST_COUNT requests successful"
    P50_MS=0
fi

# Clean up temp file
rm -f "$TEMP_FILE"

# 5) Generate verification results
OUT_JSON="${PROJECT_ROOT}/reports/phase4_migration_verify.json"

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
    "ksvc_tracked": $KSVC_TRACKED,
    "httproute_tracked": $HTTPROUTE_TRACKED
  },
  "external_access": {
    "reachable": $REACHABLE,
    "p50_ms": $P50_MS,
    "successful_requests": $SUCCESS_COUNT,
    "total_requests": $REQUEST_COUNT,
    "success_rate_percent": $((SUCCESS_COUNT * 100 / REQUEST_COUNT))
  },
  "overall_status": {
    "synced": $SYNCED,
    "healthy": $HEALTHY,
    "ksvc_tracked": $KSVC_TRACKED,
    "httproute_tracked": $HTTPROUTE_TRACKED,
    "reachable": $REACHABLE,
    "p50_ms": $P50_MS,
    "all_ok": $(if [[ "$SYNCED" == "true" && "$HEALTHY" == "true" && "$KSVC_TRACKED" == "true" && "$HTTPROUTE_TRACKED" == "true" && "$REACHABLE" == "true" ]]; then echo "true"; else echo "false"; fi)
  }
}
EOF

# Pretty print results
log_info "Migration verification results saved to: $OUT_JSON"
jq '.' "$OUT_JSON"

# 6) Generate snapshot report
log_info "Generating snapshot report..."

DATE_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT=$(git rev-parse --short HEAD)
VERIFY_JSON_REL="reports/phase4_migration_verify.json"

# Process template if it exists
TEMPLATE_FILE="${PROJECT_ROOT}/reports/templates/phase4_migration_report.md.tmpl"
SNAPSHOT_FILE="${PROJECT_ROOT}/reports/snap_phase4-3-apps-migrated.md"

if [[ -f "$TEMPLATE_FILE" ]]; then
    sed -e "s|{{DATE}}|$DATE_ISO|g" \
        -e "s|{{COMMIT}}|$COMMIT|g" \
        -e "s|{{VERIFY_JSON}}|$VERIFY_JSON_REL|g" \
        -e "s|{{SYNCED}}|$SYNCED|g" \
        -e "s|{{HEALTHY}}|$HEALTHY|g" \
        -e "s|{{KSVC_TRACKED}}|$KSVC_TRACKED|g" \
        -e "s|{{HTTPROUTE_TRACKED}}|$HTTPROUTE_TRACKED|g" \
        -e "s|{{REACHABLE}}|$REACHABLE|g" \
        -e "s|{{P50_MS}}|$P50_MS|g" \
        -e "s|{{SUCCESS_COUNT}}|$SUCCESS_COUNT|g" \
        -e "s|{{REQUEST_COUNT}}|$REQUEST_COUNT|g" \
        "$TEMPLATE_FILE" > "$SNAPSHOT_FILE"
    
    log_info "Snapshot report generated: $SNAPSHOT_FILE"
else
    log_warn "Template file not found: $TEMPLATE_FILE"
fi

# 7) Summary and exit
echo ""
echo "========================================="
echo "Migration Verification Summary"
echo "========================================="

ALL_OK=$(jq -r '.overall_status.all_ok' "$OUT_JSON")

if [[ "$ALL_OK" == "true" ]]; then
    log_info "✅ Phase 4-3 Hello Migration verification PASSED"
    log_info "   - root-app: Synced & Healthy"
    log_info "   - Knative Service 'hello': Tracked by Argo CD"
    log_info "   - HTTPRoute 'hello-route': Tracked by Argo CD" 
    log_info "   - External access: Reachable (p50: ${P50_MS}ms)"
    log_info "   - GitOps migration successfully completed"
    exit 0
else
    log_error "❌ Phase 4-3 Hello Migration verification FAILED"
    [[ "$SYNCED" != "true" ]] && log_error "   - root-app sync status: $SYNC_STATUS"
    [[ "$HEALTHY" != "true" ]] && log_error "   - root-app health status: $HEALTH_STATUS"
    [[ "$KSVC_TRACKED" != "true" ]] && log_error "   - Knative Service 'hello' not tracked"
    [[ "$HTTPROUTE_TRACKED" != "true" ]] && log_error "   - HTTPRoute 'hello-route' not tracked"
    [[ "$REACHABLE" != "true" ]] && log_error "   - External access failed"
    echo ""
    log_warn "Troubleshooting steps:"
    log_warn "   1. Check root-app sync: kubectl -n argocd get app root-app -o yaml"
    log_warn "   2. Force sync: kubectl -n argocd patch app root-app -p '{\"operation\":{\"initiatedBy\":{\"username\":\"manual\"},\"sync\":{\"syncStrategy\":{\"apply\":{\"force\":true}}}}}' --type merge"
    log_warn "   3. Check hello resources: kubectl -n hyper-swarm get ksvc,httproute"
    echo ""
    log_info "[OK] migration verify done: p50=${P50_MS}ms (with issues)"
    exit 1
fi