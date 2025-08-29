#!/usr/bin/env bash
#
# Phase 4-6: Canary Auto-Promotion with SLO Gates
# Progressively promote hello-v2 from 90:10 → 50:50 → 100:0
# Each stage validates SLO gates (p50<1000ms, success_rate≥99%)
#

set -euo pipefail

# Configuration
NS=${NS:-hyper-swarm}
RNAME=${RNAME:-hello-route}
URL=${URL:-http://localhost:31380/hello}
STAGES=("90:10" "50:50" "100:0")
OUT=reports/phase4_canary_promotion.json
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure reports directory exists
mkdir -p "$(dirname "$OUT")"

# Initialize promotion results
tmp=$(mktemp)
echo '{}' > "$OUT"

log_info() {
    echo -e "\033[32m[INFO]\033[0m $*"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $*"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $*"
}

patch_route() {
    local w1=$1
    local w2=$2
    
    log_info "Updating HTTPRoute: hello=$w1, hello-v2=$w2"
    
    kubectl -n "$NS" patch httproute "$RNAME" --type merge -p "{
        \"spec\": {
            \"rules\": [{
                \"backendRefs\": [
                    {\"kind\":\"Service\",\"name\":\"hello\",\"port\":80,\"weight\": $w1},
                    {\"kind\":\"Service\",\"name\":\"hello-v2\",\"port\":80,\"weight\": $w2}
                ]
            }]
        }
    }"
}

check_argo_sync() {
    log_info "Checking Argo CD Application sync status..."
    
    local app_status
    app_status=$(kubectl -n argocd get application root-app -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "Unknown")
    
    if [[ "$app_status" == "Synced" ]]; then
        log_info "✅ root-app is Synced"
        return 0
    else
        log_warn "⚠️  root-app sync status: $app_status"
        return 1
    fi
}

wait_for_sync() {
    log_info "Waiting for Argo CD sync and service mesh propagation..."
    
    # Wait for Argo sync
    local attempts=0
    while [[ $attempts -lt 30 ]]; do
        if check_argo_sync; then
            break
        fi
        sleep 2
        ((attempts++))
    done
    
    # Additional wait for service mesh propagation
    log_info "Waiting for service mesh propagation (10s)..."
    sleep 10
}

main() {
    echo "=" * 50
    echo "Phase 4-6: Canary Auto-Promotion"
    echo "=" * 50
    
    log_info "Starting canary promotion workflow"
    log_info "Target HTTPRoute: $NS/$RNAME"
    log_info "Test URL: $URL"
    log_info "Promotion stages: ${STAGES[*]}"
    log_info "Output: $OUT"
    
    # Initialize promotion metadata
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local commit
    commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local branch
    branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    
    # Add metadata to results
    jq -n --arg ts "$timestamp" --arg commit "$commit" --arg branch "$branch" '{
        timestamp: $ts,
        commit: $commit,
        branch: $branch,
        stages: {}
    }' > "$OUT"
    
    # Execute promotion stages
    local stage_failed=false
    
    for stage in "${STAGES[@]}"; do
        local hello_weight=${stage%:*}
        local v2_weight=${stage#*:}
        
        echo
        log_info "=== STAGE: hello=$hello_weight, hello-v2=$v2_weight ==="
        
        # Update HTTPRoute weights
        if ! patch_route "$hello_weight" "$v2_weight"; then
            log_error "Failed to update HTTPRoute for stage $stage"
            stage_failed=true
            break
        fi
        
        # Wait for synchronization
        wait_for_sync
        
        # Run SLO gate validation
        log_info "Running SLO gate validation for stage $stage..."
        if python3 "$PROJECT_ROOT/scripts/phase4_canary_gate.py" \
            --url "$URL" \
            --stage "$stage" \
            --n 300 \
            --out "$OUT"; then
            log_info "✅ SLO gate passed for stage $stage"
        else
            log_error "❌ SLO gate failed for stage $stage"
            stage_failed=true
            break
        fi
        
        # Brief pause before next stage
        if [[ "$stage" != "100:0" ]]; then
            log_info "Stage $stage completed, proceeding to next stage in 5s..."
            sleep 5
        fi
    done
    
    echo
    echo "=" * 50
    echo "Canary Promotion Summary"
    echo "=" * 50
    
    if [[ "$stage_failed" == "true" ]]; then
        log_error "❌ Canary promotion FAILED"
        log_error "Check $OUT for detailed results"
        
        # Attempt rollback to safe state (90:10)
        log_warn "Attempting rollback to safe state (90:10)..."
        patch_route 90 10 || true
        
        exit 1
    else
        log_info "✅ Canary promotion SUCCESSFUL"
        log_info "All SLO gates passed through 90→50→100% promotion"
        log_info "Final state: 100% hello-v2 traffic"
        log_info "Results saved to: $OUT"
        
        # Update final promotion status
        jq '.promotion_status = "success" | .final_stage = "100:0"' "$OUT" > "$tmp" && mv "$tmp" "$OUT"
        
        echo
        log_info "[OK] Promotion complete → $OUT"
        exit 0
    fi
}

# Rollback function for emergency use
rollback() {
    log_warn "Emergency rollback triggered"
    patch_route 90 10
    log_info "Rolled back to 90:10 (safe canary state)"
}

# Set up signal handlers for emergency rollback
trap rollback INT TERM

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi