#!/usr/bin/env bash
#
# Phase 5-3: CD Guard Rollback & Freeze
# Automatic rollback and deploy freeze on post-promotion SLO guard failure
#

set -euo pipefail

# Configuration with defaults
NS=${NS:-hyper-swarm}
ROUTE=${ROUTE:-hello-route}
PREV_STAGE=${PREV_STAGE:-50:50}  # Previous canary stage to rollback to
FREEZE_FILE=".ops/deploy_freeze.json"
GUARD_RESULT="reports/phase5_cd_guard_result.json"
ROLLBACK_LOG="reports/phase5_cd_rollback.log"

# Colors for output
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
BLUE='\033[34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$ROLLBACK_LOG"
}

log_phase() {
    echo -e "${BLUE}[PHASE]${NC} $*" | tee -a "$ROLLBACK_LOG"
}

initialize_rollback() {
    log_phase "Initializing emergency rollback procedure..."
    
    # Ensure directories exist
    mkdir -p .ops reports
    
    # Initialize rollback log
    echo "=== CD Guard Rollback Log ===" > "$ROLLBACK_LOG"
    echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$ROLLBACK_LOG"
    echo "Trigger: Post-promotion SLO guard failure" >> "$ROLLBACK_LOG"
    echo "Previous stage: $PREV_STAGE" >> "$ROLLBACK_LOG"
    echo "" >> "$ROLLBACK_LOG"
    
    log_info "Rollback procedure initialized"
    log_info "Target rollback stage: $PREV_STAGE"
    log_info "Namespace: $NS"
    log_info "HTTPRoute: $ROUTE"
}

perform_rollback() {
    log_phase "Performing traffic rollback..."
    
    # Parse previous stage weights (format: "hello_weight:hello_v2_weight")
    HELLO_WEIGHT=${PREV_STAGE%:*}
    HELLO_V2_WEIGHT=${PREV_STAGE#*:}
    
    log_info "Rolling back HTTPRoute traffic weights:"
    log_info "  hello: $HELLO_WEIGHT%"
    log_info "  hello-v2: $HELLO_V2_WEIGHT%"
    
    # Get current HTTPRoute state before rollback
    log_info "Current HTTPRoute state:"
    kubectl -n "$NS" get httproute "$ROUTE" -o jsonpath='{.spec.rules[0].backendRefs}' | jq '.' || log_warn "Could not retrieve current HTTPRoute state"
    
    # Perform the rollback
    kubectl -n "$NS" patch httproute "$ROUTE" --type merge -p "{
        \"metadata\": {
            \"annotations\": {
                \"rollback.vpm-mini.io/timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
                \"rollback.vpm-mini.io/reason\": \"post-promotion-slo-guard-failure\",
                \"rollback.vpm-mini.io/previous-stage\": \"$PREV_STAGE\"
            }
        },
        \"spec\": {
            \"rules\": [{
                \"backendRefs\": [
                    {\"kind\":\"Service\",\"name\":\"hello\",\"port\":80,\"weight\": $HELLO_WEIGHT},
                    {\"kind\":\"Service\",\"name\":\"hello-v2\",\"port\":80,\"weight\": $HELLO_V2_WEIGHT}
                ]
            }]
        }
    }"
    
    if [[ $? -eq 0 ]]; then
        log_info "✅ Traffic rollback completed successfully"
        
        # Verify rollback
        log_info "Verifying rollback state:"
        kubectl -n "$NS" get httproute "$ROUTE" -o jsonpath='{.spec.rules[0].backendRefs}' | jq '.'
        
        # Wait for rollback to take effect
        log_info "Waiting 30 seconds for traffic rollback to propagate..."
        sleep 30
        
    else
        log_error "❌ Traffic rollback failed"
        return 1
    fi
}

enable_deploy_freeze() {
    log_phase "Enabling deploy freeze..."
    
    # Create freeze configuration
    local freeze_config=$(cat <<EOF
{
  "freeze": true,
  "reason": "post-promotion-slo-guard-failure",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "rollback_stage": "$PREV_STAGE",
  "auto_created": true,
  "resolution_required": "Manual freeze resolution required - update this file to {\"freeze\": false} when ready to re-enable deployments"
}
EOF
)
    
    echo "$freeze_config" > "$FREEZE_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_info "✅ Deploy freeze enabled"
        log_warn "⚠️  All future deployments are now FROZEN until manual resolution"
        log_warn "⚠️  To resolve: Update $FREEZE_FILE to {\"freeze\": false}"
    else
        log_error "❌ Failed to enable deploy freeze"
        return 1
    fi
}

update_guard_result() {
    log_phase "Updating guard result with rollback information..."
    
    if [[ -f "$GUARD_RESULT" ]]; then
        # Add rollback information to existing guard result
        local temp_file
        temp_file=$(mktemp)
        
        jq '. + {
            "rolled_back": true,
            "freeze_on": true,
            "rollback_timestamp": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'",
            "rollback_stage": "'"$PREV_STAGE"'",
            "rollback_reason": "post-promotion-slo-guard-failure"
        }' "$GUARD_RESULT" > "$temp_file" && mv "$temp_file" "$GUARD_RESULT"
        
        log_info "✅ Guard result updated with rollback information"
    else
        # Create new guard result if it doesn't exist
        log_warn "Guard result file not found, creating minimal rollback record"
        
        cat > "$GUARD_RESULT" <<EOF
{
  "guard_ok": false,
  "rolled_back": true,
  "freeze_on": true,
  "rollback_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "rollback_stage": "$PREV_STAGE",
  "rollback_reason": "post-promotion-slo-guard-failure",
  "error": "Guard result file was missing during rollback"
}
EOF
    fi
}

verify_rollback_success() {
    log_phase "Verifying rollback success..."
    
    # Check HTTPRoute state
    local current_weights
    current_weights=$(kubectl -n "$NS" get httproute "$ROUTE" -o jsonpath='{.spec.rules[0].backendRefs}' 2>/dev/null || echo "[]")
    
    if [[ -n "$current_weights" && "$current_weights" != "[]" ]]; then
        log_info "Current traffic weights after rollback:"
        echo "$current_weights" | jq '.'
        
        # Extract actual weights and verify
        local hello_actual_weight
        local hello_v2_actual_weight
        hello_actual_weight=$(echo "$current_weights" | jq -r '.[] | select(.name=="hello") | .weight // 0')
        hello_v2_actual_weight=$(echo "$current_weights" | jq -r '.[] | select(.name=="hello-v2") | .weight // 0')
        
        local expected_hello=${PREV_STAGE%:*}
        local expected_hello_v2=${PREV_STAGE#*:}
        
        if [[ "$hello_actual_weight" == "$expected_hello" && "$hello_v2_actual_weight" == "$expected_hello_v2" ]]; then
            log_info "✅ Rollback verification successful"
            log_info "  hello: $hello_actual_weight (expected: $expected_hello)"
            log_info "  hello-v2: $hello_v2_actual_weight (expected: $expected_hello_v2)"
        else
            log_warn "⚠️  Rollback weights may not match expected values"
            log_warn "  hello: $hello_actual_weight (expected: $expected_hello)"
            log_warn "  hello-v2: $hello_v2_actual_weight (expected: $expected_hello_v2)"
        fi
    else
        log_error "❌ Could not verify rollback state"
        return 1
    fi
    
    # Check freeze state
    if [[ -f "$FREEZE_FILE" ]] && jq -e '.freeze == true' "$FREEZE_FILE" >/dev/null 2>&1; then
        log_info "✅ Deploy freeze is active"
    else
        log_warn "⚠️  Deploy freeze state could not be verified"
    fi
}

generate_rollback_summary() {
    log_phase "Generating rollback summary..."
    
    local summary_file="reports/phase5_cd_rollback_summary.json"
    
    cat > "$summary_file" <<EOF
{
  "event": "post-promotion-slo-guard-rollback",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "rollback_stage": "$PREV_STAGE",
  "actions_taken": {
    "traffic_rollback": true,
    "deploy_freeze": true,
    "guard_result_updated": true
  },
  "affected_resources": {
    "namespace": "$NS",
    "httproute": "$ROUTE",
    "freeze_file": "$FREEZE_FILE"
  },
  "next_steps": [
    "Investigate root cause of SLO guard failure",
    "Review guard result in $GUARD_RESULT",
    "Manually resolve deploy freeze when ready",
    "Consider adjusting SLO thresholds if appropriate"
  ]
}
EOF
    
    log_info "Rollback summary saved to: $summary_file"
}

main() {
    echo "=============================================="
    echo "CD Guard Rollback & Freeze Procedure"
    echo "=============================================="
    echo
    
    # Initialize
    initialize_rollback
    echo
    
    # Perform rollback
    if perform_rollback; then
        log_info "Traffic rollback completed successfully"
    else
        log_error "Traffic rollback failed - manual intervention required"
        exit 1
    fi
    echo
    
    # Enable freeze
    if enable_deploy_freeze; then
        log_info "Deploy freeze enabled successfully"
    else
        log_error "Deploy freeze failed - manual intervention required"
        exit 1
    fi
    echo
    
    # Update results
    update_guard_result
    echo
    
    # Verify success
    verify_rollback_success
    echo
    
    # Generate summary
    generate_rollback_summary
    echo
    
    log_phase "Emergency rollback procedure completed"
    log_warn "⚠️  IMPORTANT: Deployments are now FROZEN"
    log_warn "⚠️  Manual resolution required to re-enable CI/CD"
    log_info "Review logs in: $ROLLBACK_LOG"
    log_info "Review guard results in: $GUARD_RESULT"
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  -h, --help              Show this help"
        echo "  NS=<namespace>          Target namespace (default: hyper-swarm)"
        echo "  ROUTE=<route-name>      HTTPRoute name (default: hello-route)"
        echo "  PREV_STAGE=<stage>      Previous stage weights (default: 50:50)"
        echo
        echo "Environment variables:"
        echo "  NS                      Target Kubernetes namespace"
        echo "  ROUTE                   HTTPRoute resource name"
        echo "  PREV_STAGE             Previous canary stage (format: hello_weight:hello_v2_weight)"
        echo
        echo "Example:"
        echo "  NS=production ROUTE=api-route PREV_STAGE=90:10 $0"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac