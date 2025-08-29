#!/usr/bin/env bash
#
# Phase 5-4: Multi-Cluster ApplicationSet Verification
# Verify both clusters are registered, Applications are synced/healthy, and services are reachable
#

set -euo pipefail

# Configuration
OUTPUT_FILE="reports/phase5_appset_verify.json"
A_URL=${A_URL:-http://localhost:31380/hello}
B_URL=${B_URL:-http://localhost:32380/hello}
TIMEOUT=${TIMEOUT:-10}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.. && pwd)"

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

check_cluster_registration() {
    log_phase "Checking cluster registration..."
    
    local clusters_json
    clusters_json=$(kubectl -n argocd get secrets -l argocd.argoproj.io/secret-type=cluster -o json 2>/dev/null || echo '{"items":[]}')
    
    local registered_clusters
    registered_clusters=$(echo "$clusters_json" | jq -r '.items[] | @base64decode(.data.name // empty) // empty' 2>/dev/null | sort | tr '\n' ' ')
    
    log_info "Registered clusters: $registered_clusters"
    
    # Check for cluster-a and cluster-b
    local cluster_a_found=false
    local cluster_b_found=false
    
    if echo "$registered_clusters" | grep -q "cluster-a"; then
        cluster_a_found=true
        log_info "✅ cluster-a is registered"
    else
        log_error "❌ cluster-a is not registered"
    fi
    
    if echo "$registered_clusters" | grep -q "cluster-b"; then
        cluster_b_found=true
        log_info "✅ cluster-b is registered"
    else
        log_error "❌ cluster-b is not registered"
    fi
    
    echo "$cluster_a_found,$cluster_b_found"
}

check_applications_status() {
    log_phase "Checking ApplicationSet generated Applications..."
    
    # Get all applications with root-app prefix
    local applications_json
    applications_json=$(kubectl -n argocd get applications -o json 2>/dev/null || echo '{"items":[]}')
    
    # Filter applications that match root-app-* pattern
    local root_apps
    root_apps=$(echo "$applications_json" | jq -r '.items[] | select(.metadata.name | test("^root-app-")) | .metadata.name' 2>/dev/null)
    
    if [[ -z "$root_apps" ]]; then
        log_error "❌ No root-app Applications found"
        echo "false,false"
        return
    fi
    
    log_info "Found Applications: $root_apps"
    
    # Check sync status
    local all_synced=true
    local all_healthy=true
    
    while IFS= read -r app_name; do
        if [[ -n "$app_name" ]]; then
            local sync_status
            local health_status
            
            sync_status=$(echo "$applications_json" | jq -r ".items[] | select(.metadata.name == \"$app_name\") | .status.sync.status // \"Unknown\"")
            health_status=$(echo "$applications_json" | jq -r ".items[] | select(.metadata.name == \"$app_name\") | .status.health.status // \"Unknown\"")
            
            log_info "Application $app_name: sync=$sync_status, health=$health_status"
            
            if [[ "$sync_status" != "Synced" ]]; then
                all_synced=false
                log_error "❌ Application $app_name is not synced (status: $sync_status)"
            fi
            
            if [[ "$health_status" != "Healthy" ]]; then
                all_healthy=false
                log_error "❌ Application $app_name is not healthy (status: $health_status)"
            fi
        fi
    done <<< "$root_apps"
    
    if $all_synced; then
        log_info "✅ All Applications are synced"
    fi
    
    if $all_healthy; then
        log_info "✅ All Applications are healthy"
    fi
    
    echo "$all_synced,$all_healthy"
}

check_service_connectivity() {
    local url="$1"
    local cluster_name="$2"
    
    log_info "Testing connectivity to $cluster_name at $url..."
    
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")
    
    if [[ "$http_code" == "200" ]]; then
        log_info "✅ $cluster_name responded with HTTP $http_code"
        echo "true"
    else
        log_error "❌ $cluster_name responded with HTTP $http_code (or connection failed)"
        echo "false"
    fi
}

generate_verification_report() {
    local cluster_a_reg="$1"
    local cluster_b_reg="$2"
    local synced="$3"
    local healthy="$4"
    local a_http="$5"
    local b_http="$6"
    
    log_phase "Generating verification report..."
    
    # Ensure reports directory exists
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    
    # Get additional metadata
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local commit
    commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Create comprehensive verification report
    local verification_json
    verification_json=$(jq -n \
        --arg timestamp "$timestamp" \
        --arg commit "$commit" \
        --argjson cluster_a_registered "$cluster_a_reg" \
        --argjson cluster_b_registered "$cluster_b_reg" \
        --argjson synced "$synced" \
        --argjson healthy "$healthy" \
        --argjson a_http_200 "$a_http" \
        --argjson b_http_200 "$b_http" \
        --arg a_url "$A_URL" \
        --arg b_url "$B_URL" \
        '{
            timestamp: $timestamp,
            commit: $commit,
            clusters: ["cluster-a", "cluster-b"],
            cluster_registration: {
                cluster_a: $cluster_a_registered,
                cluster_b: $cluster_b_registered,
                both_registered: ($cluster_a_registered and $cluster_b_registered)
            },
            applications: {
                synced: $synced,
                healthy: $healthy,
                both_ready: ($synced and $healthy)
            },
            connectivity: {
                cluster_a: {
                    url: $a_url,
                    http_200: $a_http_200
                },
                cluster_b: {
                    url: $b_url,
                    http_200: $b_http_200
                },
                both_reachable: ($a_http_200 and $b_http_200)
            },
            overall_success: ($cluster_a_registered and $cluster_b_registered and $synced and $healthy and $a_http_200 and $b_http_200)
        }')
    
    # Write to file
    echo "$verification_json" > "$OUTPUT_FILE"
    
    log_info "✅ Verification report saved to: $OUTPUT_FILE"
    
    # Display summary
    echo
    log_phase "Multi-Cluster Verification Summary"
    echo "=================================="
    
    echo "$verification_json" | jq -r '
        "Timestamp: " + .timestamp + "\n" +
        "Commit: " + .commit + "\n" +
        "Cluster Registration: " + (if .cluster_registration.both_registered then "✅ PASS" else "❌ FAIL" end) + "\n" +
        "Application Sync: " + (if .applications.synced then "✅ SYNCED" else "❌ NOT_SYNCED" end) + "\n" +
        "Application Health: " + (if .applications.healthy then "✅ HEALTHY" else "❌ UNHEALTHY" end) + "\n" +
        "Cluster A HTTP: " + (if .connectivity.cluster_a.http_200 then "✅ 200" else "❌ FAIL" end) + " (" + .connectivity.cluster_a.url + ")" + "\n" +
        "Cluster B HTTP: " + (if .connectivity.cluster_b.http_200 then "✅ 200" else "❌ FAIL" end) + " (" + .connectivity.cluster_b.url + ")" + "\n" +
        "Overall Success: " + (if .overall_success then "✅ PASS" else "❌ FAIL" end)
    '
    
    # Return overall success status
    if echo "$verification_json" | jq -e '.overall_success' >/dev/null; then
        return 0
    else
        return 1
    fi
}

generate_snapshot() {
    log_phase "Generating snapshot report..."
    
    local template_file="reports/templates/phase5_appset_report.md.tmpl"
    local snapshot_file="reports/snap_phase5-4-multicluster.md"
    
    if [[ ! -f "$template_file" ]]; then
        log_warn "Template file not found: $template_file"
        log_info "Creating basic snapshot without template"
        
        cat > "$snapshot_file" <<EOF
# Phase 5-4: Multi-Cluster GitOps (ApplicationSet) - Verification Report

**Date**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Commit**: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")  
**Verification**: $OUTPUT_FILE

## Results
$(jq -r '
if .overall_success then
  "✅ **PASS** - Multi-cluster GitOps successfully configured\n\n" +
  "- Applications: root-app-cluster-a / root-app-cluster-b → Synced & Healthy\n" +
  "- External: cluster-a(" + (.connectivity.cluster_a.url | split("//")[1] | split("/")[0]) + ") / cluster-b(" + (.connectivity.cluster_b.url | split("//")[1] | split("/")[0]) + ") both HTTP 200"
else
  "❌ **FAIL** - Multi-cluster setup incomplete\n\n" +
  "- Check verification results in " + "'$OUTPUT_FILE'"
end
' "$OUTPUT_FILE")

## Implementation
- **ApplicationSet**: Deployed to generate root-app-<cluster> applications
- **Cluster Registration**: Both cluster-a and cluster-b registered with region labels
- **Traffic Differentiation**: NodePort 31380 (cluster-a) and 32380 (cluster-b)
- **GitOps Sync**: Automated synchronization of infra/gitops/apps/ to both clusters
EOF
        
    else
        # Use template file if available
        local date_iso
        local commit
        date_iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        
        sed -e "s|{{DATE}}|$date_iso|g" \
            -e "s|{{COMMIT}}|$commit|g" \
            -e "s|{{VERIFY_JSON}}|$OUTPUT_FILE|g" \
            "$template_file" > "$snapshot_file"
    fi
    
    log_info "✅ Snapshot generated: $snapshot_file"
}

main() {
    echo "=============================================="
    echo "Phase 5-4: Multi-Cluster ApplicationSet Verification"
    echo "=============================================="
    echo
    echo "Configuration:"
    echo "  Cluster A URL: $A_URL"
    echo "  Cluster B URL: $B_URL"
    echo "  Timeout: ${TIMEOUT}s"
    echo "  Output: $OUTPUT_FILE"
    echo
    
    # Check cluster registration
    local cluster_registration
    cluster_registration=$(check_cluster_registration)
    local cluster_a_reg=$(echo "$cluster_registration" | cut -d, -f1)
    local cluster_b_reg=$(echo "$cluster_registration" | cut -d, -f2)
    echo
    
    # Check ApplicationSet generated Applications
    local app_status
    app_status=$(check_applications_status)
    local synced=$(echo "$app_status" | cut -d, -f1)
    local healthy=$(echo "$app_status" | cut -d, -f2)
    echo
    
    # Check service connectivity
    log_phase "Testing service connectivity..."
    local a_http
    local b_http
    a_http=$(check_service_connectivity "$A_URL" "cluster-a")
    b_http=$(check_service_connectivity "$B_URL" "cluster-b")
    echo
    
    # Generate verification report
    if generate_verification_report "$cluster_a_reg" "$cluster_b_reg" "$synced" "$healthy" "$a_http" "$b_http"; then
        log_info "🎉 Multi-cluster verification PASSED"
        verification_success=true
    else
        log_error "❌ Multi-cluster verification FAILED"
        verification_success=false
    fi
    echo
    
    # Generate snapshot
    generate_snapshot
    echo
    
    log_phase "Verification completed!"
    log_info "Results available in: $OUTPUT_FILE"
    
    # Exit with appropriate code
    if [[ "$verification_success" == "true" ]]; then
        exit 0
    else
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  -h, --help              Show this help"
        echo "  A_URL=<url>             Cluster A service URL (default: http://localhost:31380/hello)"
        echo "  B_URL=<url>             Cluster B service URL (default: http://localhost:32380/hello)"
        echo "  TIMEOUT=<seconds>       HTTP request timeout (default: 10)"
        echo
        echo "Example:"
        echo "  A_URL=http://prod-east:31380/hello B_URL=http://prod-west:32380/hello $0"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac