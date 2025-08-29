#!/usr/bin/env bash
#
# Phase 4 Exit Verification Script
# Comprehensive validation of all Phase 4 deliverables and success criteria
#

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"
CANARY_JSON="${CANARY_JSON:-$REPORTS_DIR/phase4_canary_promotion.json}"
SCALE_JSON="${SCALE_JSON:-$REPORTS_DIR/phase4_scale_verify.json}"
OUT_JSON="$REPORTS_DIR/phase4_exit_result.json"
SNAP_MD="$REPORTS_DIR/snap_phase4-complete.md"
TEMPLATE_MD="$REPORTS_DIR/templates/phase4_exit_checklist.md.tmpl"

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $*"
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check required commands
    for cmd in kubectl jq git; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check required files
    if [[ ! -f "$CANARY_JSON" ]]; then
        log_error "Canary promotion results not found: $CANARY_JSON"
        exit 1
    fi
    
    if [[ ! -f "$SCALE_JSON" ]]; then
        log_error "Scale verification results not found: $SCALE_JSON"
        exit 1
    fi
    
    if [[ ! -f "$TEMPLATE_MD" ]]; then
        log_error "Exit checklist template not found: $TEMPLATE_MD"
        exit 1
    fi
    
    log_info "✅ Prerequisites check passed"
}

verify_gitops_status() {
    log_step "Verifying GitOps status (Argo CD root-app)..."
    
    # Get root-app Application status
    if ! APP_JSON=$(kubectl -n argocd get application root-app -o json 2>/dev/null); then
        log_error "Failed to get root-app Application status"
        return 1
    fi
    
    # Check sync status
    SYNC_STATUS=$(echo "$APP_JSON" | jq -r '.status.sync.status // "Unknown"')
    SYNCED=$(echo "$APP_JSON" | jq -r '.status.sync.status=="Synced"')
    
    # Check health status  
    HEALTH_STATUS=$(echo "$APP_JSON" | jq -r '.status.health.status // "Unknown"')
    HEALTHY=$(echo "$APP_JSON" | jq -r '.status.health.status=="Healthy"')
    
    log_info "Sync Status: $SYNC_STATUS (Synced: $SYNCED)"
    log_info "Health Status: $HEALTH_STATUS (Healthy: $HEALTHY)"
    
    if [[ "$SYNCED" == "true" ]]; then
        log_info "✅ root-app is Synced"
    else
        log_warn "⚠️  root-app is not Synced: $SYNC_STATUS"
    fi
    
    if [[ "$HEALTHY" == "true" ]]; then
        log_info "✅ root-app is Healthy"
    else
        log_warn "⚠️  root-app is not Healthy: $HEALTH_STATUS"
    fi
    
    echo "$APP_JSON"
}

verify_network_boundary() {
    log_step "Verifying network boundary configuration..."
    
    local app_json="$1"
    
    # Check Gateway tracking
    GATEWAY_NAME=$(echo "$app_json" | jq -r '.status.resources[]? | select(.kind=="Gateway") | .name' | head -1)
    GATEWAY_TRACKED="false"
    
    if [[ -n "$GATEWAY_NAME" ]] && [[ "$GATEWAY_NAME" == "vpm-mini-gateway" ]]; then
        GATEWAY_TRACKED="true"
        log_info "✅ Gateway tracked: $GATEWAY_NAME"
    else
        log_warn "⚠️  Expected Gateway vpm-mini-gateway not found. Found: $GATEWAY_NAME"
    fi
    
    # Check NetworkPolicy count
    NETPOL_COUNT=$(echo "$app_json" | jq -r '[.status.resources[]? | select(.kind=="NetworkPolicy")] | length')
    NETPOL_SUFFICIENT="false"
    
    if [[ "$NETPOL_COUNT" -ge 2 ]]; then
        NETPOL_SUFFICIENT="true"
        log_info "✅ NetworkPolicy count: $NETPOL_COUNT (≥2 required)"
    else
        log_warn "⚠️  NetworkPolicy count: $NETPOL_COUNT (<2 required)"
    fi
    
    # List NetworkPolicies for reference
    if [[ "$NETPOL_COUNT" -gt 0 ]]; then
        NETPOL_NAMES=$(echo "$app_json" | jq -r '.status.resources[]? | select(.kind=="NetworkPolicy") | .name' | tr '\n' ', ' | sed 's/,$//')
        log_info "NetworkPolicies tracked: $NETPOL_NAMES"
    fi
    
    echo "$GATEWAY_TRACKED $NETPOL_SUFFICIENT"
}

verify_canary_deployment() {
    log_step "Verifying canary deployment results..."
    
    if [[ ! -f "$CANARY_JSON" ]]; then
        log_error "Canary results file not found: $CANARY_JSON"
        return 1
    fi
    
    log_info "Analyzing canary promotion results: $CANARY_JSON"
    
    # Check stage gates
    STAGE_90_10=$(jq -r '.stages."90:10".gate_ok // false' "$CANARY_JSON")
    STAGE_50_50=$(jq -r '.stages."50:50".gate_ok // false' "$CANARY_JSON")
    STAGE_100_0=$(jq -r '.stages."100:0".gate_ok // false' "$CANARY_JSON")
    FINAL_OK=$(jq -r '.stages."100:0".final_ok // false' "$CANARY_JSON")
    V2_SHARE=$(jq -r '.stages."100:0".v2_share // 0' "$CANARY_JSON")
    
    log_info "Stage 90:10 gate: $STAGE_90_10"
    log_info "Stage 50:50 gate: $STAGE_50_50"
    log_info "Stage 100:0 gate: $STAGE_100_0"
    log_info "Final gate: $FINAL_OK"
    log_info "V2 share: $V2_SHARE"
    
    # Comprehensive canary validation
    CANARY_GATES_OK=$(jq -r '
        ([.stages."90:10".gate_ok, .stages."50:50".gate_ok] | all) and
        (.stages."100:0".gate_ok // true) and 
        (.stages."100:0".final_ok // true) and
        ((.stages."100:0".v2_share // 0) >= 0.95)
    ' "$CANARY_JSON")
    
    if [[ "$CANARY_GATES_OK" == "true" ]]; then
        log_info "✅ Canary deployment validation passed"
        log_info "   - All stage gates: PASS"
        log_info "   - Final V2 share: $V2_SHARE (≥0.95)"
    else
        log_warn "⚠️  Canary deployment validation failed"
        [[ "$STAGE_90_10" != "true" ]] && log_warn "   - Stage 90:10 gate failed"
        [[ "$STAGE_50_50" != "true" ]] && log_warn "   - Stage 50:50 gate failed"
        [[ "$STAGE_100_0" != "true" ]] && log_warn "   - Stage 100:0 gate failed"
        [[ "$FINAL_OK" != "true" ]] && log_warn "   - Final gate failed"
        [[ $(echo "$V2_SHARE < 0.95" | bc -l) == "1" ]] && log_warn "   - V2 share insufficient: $V2_SHARE < 0.95"
    fi
    
    echo "$CANARY_GATES_OK"
}

verify_high_load_performance() {
    log_step "Verifying high-load performance results..."
    
    if [[ ! -f "$SCALE_JSON" ]]; then
        log_error "Scale verification file not found: $SCALE_JSON"
        return 1
    fi
    
    log_info "Analyzing scale verification results: $SCALE_JSON"
    
    # Extract performance metrics
    CLIENT_RPS=$(jq -r '.performance_metrics.client_rps // 0' "$SCALE_JSON")
    MEETS_RPS=$(jq -r '.test_summary.meets_rps_requirement // false' "$SCALE_JSON")
    MEETS_SLO=$(jq -r '.test_summary.meets_slo_requirements // false' "$SCALE_JSON")
    MEETS_DURATION=$(jq -r '.test_summary.meets_duration_requirement // false' "$SCALE_JSON")
    SCALING_OCCURRED=$(jq -r '.test_summary.scaling_occurred // false' "$SCALE_JSON")
    OVERALL_SUCCESS=$(jq -r '.test_summary.overall_success // false' "$SCALE_JSON")
    
    # SLO details
    P50_MS=$(jq -r '.slo_metrics.p50_ms // 0' "$SCALE_JSON")
    P95_MS=$(jq -r '.slo_metrics.p95_ms // 0' "$SCALE_JSON")
    SUCCESS_RATE=$(jq -r '.slo_metrics.success_rate // 0' "$SCALE_JSON")
    CURRENT_PODS=$(jq -r '.scaling_metrics.current_pods // 0' "$SCALE_JSON")
    
    log_info "Performance metrics:"
    log_info "   - Client RPS: $CLIENT_RPS"
    log_info "   - Meets RPS (≥800): $MEETS_RPS"
    log_info "   - Meets SLO: $MEETS_SLO"
    log_info "   - Meets Duration: $MEETS_DURATION"
    log_info "   - Scaling Occurred: $SCALING_OCCURRED ($CURRENT_PODS pods)"
    log_info "   - P50 latency: ${P50_MS}ms"
    log_info "   - P95 latency: ${P95_MS}ms"
    log_info "   - Success rate: $(echo "$SUCCESS_RATE * 100" | bc -l 2>/dev/null || echo "$SUCCESS_RATE")%"
    
    # Load test validation
    LOAD_VALIDATION=$(jq -r '
        .test_summary.meets_rps_requirement and 
        .test_summary.meets_slo_requirements
    ' "$SCALE_JSON")
    
    if [[ "$LOAD_VALIDATION" == "true" ]]; then
        log_info "✅ High-load performance validation passed"
        log_info "   - RPS requirement: $MEETS_RPS (≥800 RPS)"
        log_info "   - SLO compliance: $MEETS_SLO"
    else
        log_warn "⚠️  High-load performance validation failed"
        [[ "$MEETS_RPS" != "true" ]] && log_warn "   - RPS requirement failed: $CLIENT_RPS < 800"
        [[ "$MEETS_SLO" != "true" ]] && log_warn "   - SLO compliance failed"
    fi
    
    echo "$LOAD_VALIDATION"
}

generate_exit_results() {
    log_step "Generating Phase 4 exit results..."
    
    local synced="$1"
    local healthy="$2"
    local gateway_tracked="$3"
    local netpol_sufficient="$4"
    local canary_ok="$5"
    local load_ok="$6"
    
    # Calculate overall success
    ALL_OK="false"
    if [[ "$synced" == "true" ]] && [[ "$healthy" == "true" ]] && \
       [[ "$gateway_tracked" == "true" ]] && [[ "$netpol_sufficient" == "true" ]] && \
       [[ "$canary_ok" == "true" ]] && [[ "$load_ok" == "true" ]]; then
        ALL_OK="true"
    fi
    
    # Get git information
    COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Generate comprehensive results JSON
    jq -n \
        --arg timestamp "$TIMESTAMP" \
        --arg commit "$COMMIT" \
        --arg branch "$BRANCH" \
        --argjson synced "$(echo "$synced" | tr '[:lower:]' '[:lower:]')" \
        --argjson healthy "$(echo "$healthy" | tr '[:lower:]' '[:lower:]')" \
        --argjson gateway_tracked "$(echo "$gateway_tracked" | tr '[:lower:]' '[:lower:]')" \
        --argjson netpol_sufficient "$(echo "$netpol_sufficient" | tr '[:lower:]' '[:lower:]')" \
        --argjson canary_ok "$(echo "$canary_ok" | tr '[:lower:]' '[:lower:]')" \
        --argjson load_ok "$(echo "$load_ok" | tr '[:lower:]' '[:lower:]')" \
        --argjson all_ok "$(echo "$ALL_OK" | tr '[:lower:]' '[:lower:]')" \
        '{
            timestamp: $timestamp,
            commit: $commit,
            branch: $branch,
            validation_results: {
                root_app_synced: $synced,
                root_app_healthy: $healthy,
                gateway_tracked: $gateway_tracked,
                netpol_tracked: $netpol_sufficient,
                canary_deployment_ok: $canary_ok,
                high_load_performance_ok: $load_ok
            },
            phase4_exit_criteria: {
                gitops_status: ($synced and $healthy),
                network_boundary: ($gateway_tracked and $netpol_sufficient),
                canary_deployment: $canary_ok,
                high_load_performance: $load_ok,
                all_criteria_met: $all_ok
            },
            summary: {
                all_ok: $all_ok,
                total_checks: 6,
                passed_checks: (($synced | if . then 1 else 0 end) + ($healthy | if . then 1 else 0 end) + ($gateway_tracked | if . then 1 else 0 end) + ($netpol_sufficient | if . then 1 else 0 end) + ($canary_ok | if . then 1 else 0 end) + ($load_ok | if . then 1 else 0 end)),
                phase4_status: (if $all_ok then "COMPLETE" else "INCOMPLETE" end)
            }
        }' > "$OUT_JSON"
    
    log_info "Exit results saved to: $OUT_JSON"
    
    # Display summary
    PASSED_CHECKS=$(jq -r '.summary.passed_checks' "$OUT_JSON")
    TOTAL_CHECKS=$(jq -r '.summary.total_checks' "$OUT_JSON")
    PHASE4_STATUS=$(jq -r '.summary.phase4_status' "$OUT_JSON")
    
    echo
    log_step "Phase 4 Exit Summary"
    echo "===================="
    echo "✅ Passed: $PASSED_CHECKS/$TOTAL_CHECKS checks"
    echo "📊 Status: $PHASE4_STATUS"
    echo
    
    if [[ "$ALL_OK" == "true" ]]; then
        log_info "🎉 Phase 4 Exit: ALL GREEN"
    else
        log_warn "⚠️  Phase 4 Exit: SOME ISSUES DETECTED"
    fi
    
    echo "$ALL_OK"
}

generate_exit_snapshot() {
    log_step "Generating Phase 4 exit snapshot..."
    
    if [[ ! -f "$TEMPLATE_MD" ]]; then
        log_error "Template not found: $TEMPLATE_MD"
        return 1
    fi
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local commit
    commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Generate snapshot from template
    sed -e "s|{{DATE}}|$timestamp|g" \
        -e "s|{{COMMIT}}|$commit|g" \
        -e "s|{{RESULT_JSON}}|phase4_exit_result.json|g" \
        "$TEMPLATE_MD" > "$SNAP_MD"
    
    log_info "✅ Phase 4 exit snapshot generated: $SNAP_MD"
}

main() {
    echo "========================================"
    echo "Phase 4 Exit Verification"
    echo "========================================"
    echo
    
    # Check prerequisites
    check_prerequisites
    echo
    
    # 1. Verify GitOps status
    APP_JSON=$(verify_gitops_status)
    SYNCED=$(echo "$APP_JSON" | jq -r '.status.sync.status=="Synced"')
    HEALTHY=$(echo "$APP_JSON" | jq -r '.status.health.status=="Healthy"')
    echo
    
    # 2. Verify network boundary
    NETWORK_RESULT=$(verify_network_boundary "$APP_JSON")
    GATEWAY_TRACKED=$(echo "$NETWORK_RESULT" | cut -d' ' -f1)
    NETPOL_SUFFICIENT=$(echo "$NETWORK_RESULT" | cut -d' ' -f2)
    echo
    
    # 3. Verify canary deployment
    CANARY_OK=$(verify_canary_deployment)
    echo
    
    # 4. Verify high-load performance
    LOAD_OK=$(verify_high_load_performance)
    echo
    
    # 5. Generate exit results
    ALL_OK=$(generate_exit_results "$SYNCED" "$HEALTHY" "$GATEWAY_TRACKED" "$NETPOL_SUFFICIENT" "$CANARY_OK" "$LOAD_OK")
    echo
    
    # 6. Generate snapshot
    generate_exit_snapshot
    echo
    
    # Final exit
    echo "========================================"
    if [[ "$ALL_OK" == "true" ]]; then
        log_info "🎉 Phase 4 Exit: ALL GREEN - Ready for Phase 5!"
        exit 0
    else
        log_error "❌ Phase 4 Exit: ISSUES DETECTED - Review before proceeding"
        exit 1
    fi
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi