#!/bin/bash
set -euo pipefail

# Phase 3-4 Chaos Pod Kill Script
# Randomly kill pods matching a selector at specified intervals

NAMESPACE=""
SELECTOR=""
INTERVAL=20
DURATION=180
DRY_RUN=false

usage() {
    cat <<EOF
Usage: $0 --ns NAMESPACE --selector SELECTOR [OPTIONS]

Chaos engineering script that randomly kills pods matching a selector.

Required:
  --ns NAMESPACE            Kubernetes namespace to target
  --selector SELECTOR       Label selector for target pods (e.g., 'app=hello')

Options:
  --interval SECONDS        Interval between pod kills (default: 20)
  --duration SECONDS        Total duration to run chaos (default: 180)  
  --dry-run                 Show which pods would be killed without actually killing them
  -h, --help               Show this help message

Examples:
  $0 --ns default --selector 'app.kubernetes.io/name=hello' --interval 30 --duration 300
  $0 --ns hyper-swarm --selector 'app=planner' --dry-run

Safety:
  - Will not kill pods in kube-system, kube-public, or kube-node-lease namespaces
  - Requires at least 2 pods matching selector before killing any
  - Kills maximum 1 pod per interval
EOF
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ns)
            NAMESPACE="$2"
            shift 2
            ;;
        --selector)
            SELECTOR="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$NAMESPACE" ]]; then
    echo "Error: --ns NAMESPACE is required" >&2
    usage >&2
    exit 1
fi

if [[ -z "$SELECTOR" ]]; then
    echo "Error: --selector SELECTOR is required" >&2
    usage >&2
    exit 1
fi

# Safety check: prevent targeting system namespaces
case "$NAMESPACE" in
    kube-system|kube-public|kube-node-lease)
        echo "Error: Cannot target system namespace '$NAMESPACE' for safety reasons" >&2
        exit 1
        ;;
esac

log "🔥 Starting pod kill chaos scenario"
log "   Namespace: $NAMESPACE"
log "   Selector: $SELECTOR"
log "   Interval: ${INTERVAL}s"
log "   Duration: ${DURATION}s"
log "   Dry run: $DRY_RUN"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is required but not installed" >&2
    exit 1
fi

# Verify namespace exists
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
    echo "Error: Namespace '$NAMESPACE' does not exist" >&2
    exit 1
fi

# Main chaos loop
start_time=$(date +%s)
end_time=$((start_time + DURATION))
kill_count=0

log "⏰ Chaos scenario will run until $(date -d "@$end_time" '+%Y-%m-%d %H:%M:%S')"

while [[ $(date +%s) -lt $end_time ]]; do
    current_time=$(date +%s)
    remaining_time=$((end_time - current_time))
    
    log "⏳ Time remaining: ${remaining_time}s"
    
    # Get list of pods matching the selector
    pod_list=$(kubectl get pods -n "$NAMESPACE" -l "$SELECTOR" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true)
    
    if [[ -z "$pod_list" ]]; then
        log "⚠️  No running pods found matching selector '$SELECTOR' in namespace '$NAMESPACE'"
    else
        # Convert to array
        pod_array=($pod_list)
        pod_count=${#pod_array[@]}
        
        log "📊 Found $pod_count running pods matching selector"
        
        # Safety check: require at least 2 pods before killing any
        if [[ $pod_count -lt 2 ]]; then
            log "🛡️  Safety check: Only $pod_count pod(s) available, skipping kill to maintain availability"
        else
            # Select random pod to kill
            random_index=$((RANDOM % pod_count))
            target_pod="${pod_array[$random_index]}"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                log "🧪 DRY RUN: Would kill pod '$target_pod' in namespace '$NAMESPACE'"
            else
                log "💀 Killing pod '$target_pod' in namespace '$NAMESPACE'"
                if kubectl delete pod "$target_pod" -n "$NAMESPACE" --wait=false; then
                    kill_count=$((kill_count + 1))
                    log "✅ Successfully initiated deletion of pod '$target_pod'"
                else
                    log "❌ Failed to kill pod '$target_pod'"
                fi
            fi
        fi
    fi
    
    # Wait for next interval (unless we're at the end)
    if [[ $((current_time + INTERVAL)) -lt $end_time ]]; then
        log "😴 Sleeping for ${INTERVAL}s until next chaos event..."
        sleep "$INTERVAL"
    else
        # Calculate remaining sleep time
        remaining_sleep=$((end_time - $(date +%s)))
        if [[ $remaining_sleep -gt 0 ]]; then
            log "😴 Sleeping for final ${remaining_sleep}s..."
            sleep "$remaining_sleep"
        fi
        break
    fi
done

log "🏁 Chaos scenario completed"
log "   Total duration: ${DURATION}s"
log "   Pods killed: $kill_count"
log "   Target namespace: $NAMESPACE"
log "   Target selector: $SELECTOR"

# Generate summary report
summary_file="/tmp/podkill_chaos_summary.json"
cat > "$summary_file" <<EOF
{
  "chaos_type": "pod-kill",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "config": {
    "namespace": "$NAMESPACE",
    "selector": "$SELECTOR",
    "interval_seconds": $INTERVAL,
    "duration_seconds": $DURATION,
    "dry_run": $DRY_RUN
  },
  "results": {
    "pods_killed": $kill_count,
    "kill_rate": $(awk "BEGIN {printf \"%.3f\", $kill_count / ($DURATION / $INTERVAL)}")
  }
}
EOF

log "📋 Summary report saved to: $summary_file"

if [[ "$DRY_RUN" == "true" ]]; then
    log "🧪 Dry run completed - no actual pods were harmed"
else
    log "✅ Chaos scenario completed successfully"
fi