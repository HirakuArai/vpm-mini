#!/usr/bin/env bash
#
# Phase 5-1: SLO Alert Verification Script  
# Collect alert firing/recovery states and validate SLO monitoring
#

set -euo pipefail

# Configuration
PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:31390}
ALERTMANAGER_URL=${ALERTMANAGER_URL:-http://localhost:31393}
CHECK_DURATION=${CHECK_DURATION:-300}  # 5 minutes monitoring
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

check_prerequisites() {
    log_phase "Checking SLO monitoring prerequisites..."
    
    # Check if Prometheus is accessible
    if ! curl -f -s -o /dev/null "$PROMETHEUS_URL/api/v1/status/config"; then
        log_error "Prometheus not accessible at $PROMETHEUS_URL"
        log_error "Please ensure Prometheus is running and port-forwarded"
        log_info "Run: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 31390:9090"
        exit 1
    fi
    
    # Check if Alertmanager is accessible
    if ! curl -f -s -o /dev/null "$ALERTMANAGER_URL/api/v1/status"; then
        log_error "Alertmanager not accessible at $ALERTMANAGER_URL"
        log_error "Please ensure Alertmanager is running and port-forwarded"
        log_info "Run: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 31393:9093"
        exit 1
    fi
    
    log_info "✅ Prometheus accessible at $PROMETHEUS_URL"
    log_info "✅ Alertmanager accessible at $ALERTMANAGER_URL"
}

query_prometheus() {
    local query="$1"
    local result
    
    result=$(curl -s "$PROMETHEUS_URL/api/v1/query" \
        --data-urlencode "query=$query" \
        --get 2>/dev/null || echo '{"status":"error"}')
        
    echo "$result"
}

get_alert_state() {
    local alertname="$1"
    local result
    
    result=$(query_prometheus "ALERTS{alertname=\"$alertname\"}")
    
    if echo "$result" | jq -e '.status == "success"' >/dev/null 2>&1; then
        local alert_count
        alert_count=$(echo "$result" | jq -r '.data.result | length')
        
        if [[ "$alert_count" -gt 0 ]]; then
            # Check if any alerts are firing
            local firing_count
            firing_count=$(echo "$result" | jq -r '.data.result | map(select(.metric.alertstate == "firing")) | length')
            
            if [[ "$firing_count" -gt 0 ]]; then
                echo "firing"
                return
            fi
        fi
    fi
    
    echo "resolved"
}

get_current_sli_metrics() {
    log_info "Querying current SLI metrics..."
    
    # Get current error rates
    local error_rate_5m
    error_rate_5m=$(query_prometheus 'sli:http_error_rate:5m{service="hello"}' | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    local error_rate_30m
    error_rate_30m=$(query_prometheus 'sli:http_error_rate:30m{service="hello"}' | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    local error_rate_1h
    error_rate_1h=$(query_prometheus 'sli:http_error_rate:1h{service="hello"}' | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    # Get success rates
    local success_rate_5m
    success_rate_5m=$(query_prometheus 'sli:http_success_rate:5m{service="hello"}' | \
        jq -r '.data.result[0].value[1] // "1"' 2>/dev/null || echo "1")
    
    # Convert to percentages for display
    local error_pct_5m
    error_pct_5m=$(echo "$error_rate_5m * 100" | bc -l 2>/dev/null | head -c 6)
    
    local success_pct_5m
    success_pct_5m=$(echo "$success_rate_5m * 100" | bc -l 2>/dev/null | head -c 6)
    
    log_info "Current SLI metrics:"
    log_info "  Error rate (5m): ${error_pct_5m}%"
    log_info "  Success rate (5m): ${success_pct_5m}%"
    
    # Store metrics for reporting
    echo "$error_rate_5m,$error_rate_30m,$error_rate_1h,$success_rate_5m"
}

monitor_alerts() {
    local duration="$1"
    
    log_phase "Monitoring SLO alerts for ${duration}s..."
    
    local end_time=$((SECONDS + duration))
    local check_interval=15
    local check_count=0
    
    # Initialize alert detection flags
    local fast_burn_detected=false
    local slow_burn_detected=false
    local trend_warning_detected=false
    local fast_burn_resolved=false
    local slow_burn_resolved=false
    
    # Store alert timeline
    declare -a alert_timeline=()
    
    while [[ $SECONDS -lt $end_time ]]; do
        check_count=$((check_count + 1))
        local timestamp
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        log_info "Alert check $check_count (${timestamp})"
        
        # Check each alert type
        local fast_burn_state
        fast_burn_state=$(get_alert_state "SLOFastBurn")
        
        local slow_burn_state
        slow_burn_state=$(get_alert_state "SLOSlowBurn")
        
        local trend_warning_state
        trend_warning_state=$(get_alert_state "SLOErrorBudgetLow")
        
        # Log current states
        log_info "  Fast Burn Alert: $fast_burn_state"
        log_info "  Slow Burn Alert: $slow_burn_state"
        log_info "  Trend Warning: $trend_warning_state"
        
        # Update detection flags
        if [[ "$fast_burn_state" == "firing" ]]; then
            if [[ "$fast_burn_detected" != "true" ]]; then
                log_info "🚨 Fast burn alert TRIGGERED at $timestamp"
                fast_burn_detected=true
            fi
        else
            if [[ "$fast_burn_detected" == "true" && "$fast_burn_resolved" != "true" ]]; then
                log_info "✅ Fast burn alert RESOLVED at $timestamp"
                fast_burn_resolved=true
            fi
        fi
        
        if [[ "$slow_burn_state" == "firing" ]]; then
            if [[ "$slow_burn_detected" != "true" ]]; then
                log_info "⚠️ Slow burn alert TRIGGERED at $timestamp"
                slow_burn_detected=true
            fi
        else
            if [[ "$slow_burn_detected" == "true" && "$slow_burn_resolved" != "true" ]]; then
                log_info "✅ Slow burn alert RESOLVED at $timestamp"
                slow_burn_resolved=true
            fi
        fi
        
        if [[ "$trend_warning_state" == "firing" ]]; then
            if [[ "$trend_warning_detected" != "true" ]]; then
                log_info "📈 Trend warning TRIGGERED at $timestamp"
                trend_warning_detected=true
            fi
        fi
        
        # Store timeline entry
        alert_timeline+=("$timestamp,$fast_burn_state,$slow_burn_state,$trend_warning_state")
        
        # Get current metrics
        local metrics
        metrics=$(get_current_sli_metrics)
        echo
        
        sleep $check_interval
    done
    
    # Return detection results
    echo "$fast_burn_detected,$slow_burn_detected,$trend_warning_detected,$fast_burn_resolved,$slow_burn_resolved"
}

query_alertmanager_alerts() {
    log_info "Querying Alertmanager for current alerts..."
    
    local alerts_result
    alerts_result=$(curl -s "$ALERTMANAGER_URL/api/v1/alerts" 2>/dev/null || echo '{"status":"error"}')
    
    if echo "$alerts_result" | jq -e '.status == "success"' >/dev/null 2>&1; then
        local slo_alerts
        slo_alerts=$(echo "$alerts_result" | jq -r '
            .data[] | 
            select(.labels.alertname | startswith("SLO")) |
            "\(.labels.alertname): \(.status.state) since \(.startsAt)"' 2>/dev/null || echo "No SLO alerts found")
        
        if [[ -n "$slo_alerts" && "$slo_alerts" != "No SLO alerts found" ]]; then
            log_info "Active SLO alerts from Alertmanager:"
            echo "$slo_alerts" | while IFS= read -r line; do
                log_info "  $line"
            done
        else
            log_info "No active SLO alerts in Alertmanager"
        fi
    else
        log_warn "Could not query Alertmanager alerts"
    fi
}

generate_verification_report() {
    local detection_results="$1"
    
    log_phase "Generating verification report..."
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local commit
    commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Parse detection results
    IFS=',' read -r fast_burn_detected slow_burn_detected trend_warning_detected fast_burn_resolved slow_burn_resolved <<< "$detection_results"
    
    # Create verification report
    local verification_json
    verification_json=$(jq -n \
        --arg timestamp "$timestamp" \
        --arg commit "$commit" \
        --argjson fast_burn_triggered "$(echo "$fast_burn_detected" | tr '[:upper:]' '[:lower:]')" \
        --argjson slow_burn_triggered "$(echo "$slow_burn_detected" | tr '[:upper:]' '[:lower:]')" \
        --argjson trend_warning_triggered "$(echo "$trend_warning_detected" | tr '[:upper:]' '[:lower:]')" \
        --argjson fast_burn_recovered "$(echo "$fast_burn_resolved" | tr '[:upper:]' '[:lower:]')" \
        --argjson slow_burn_recovered "$(echo "$slow_burn_resolved" | tr '[:upper:]' '[:lower:]')" \
        '{
            timestamp: $timestamp,
            commit: $commit,
            verification_config: {
                prometheus_url: "'$PROMETHEUS_URL'",
                alertmanager_url: "'$ALERTMANAGER_URL'",
                check_duration: '$CHECK_DURATION'
            },
            alert_verification: {
                fast_burn_triggered: $fast_burn_triggered,
                slow_burn_triggered: $slow_burn_triggered,
                trend_warning_triggered: $trend_warning_triggered,
                fast_burn_recovered: $fast_burn_recovered,
                slow_burn_recovered: $slow_burn_recovered,
                verification_completed: true
            },
            validation: {
                alert_system_working: ($fast_burn_triggered or $slow_burn_triggered or $trend_warning_triggered),
                recovery_working: ($fast_burn_recovered or $slow_burn_recovered),
                all_ok: (
                    ($fast_burn_triggered or $slow_burn_triggered or $trend_warning_triggered) and
                    ($fast_burn_recovered or $slow_burn_recovered)
                )
            }
        }')
    
    local output_file="$PROJECT_ROOT/reports/phase5_slo_alert_verify.json"
    echo "$verification_json" > "$output_file"
    
    log_info "✅ Verification results saved to: $output_file"
    
    # Display summary
    echo
    log_phase "Alert Verification Summary"
    echo "=========================="
    jq -r '
        "Fast Burn Triggered: " + (if .alert_verification.fast_burn_triggered then "✅ YES" else "❌ NO" end) + "\n" +
        "Slow Burn Triggered: " + (if .alert_verification.slow_burn_triggered then "✅ YES" else "❌ NO" end) + "\n" +
        "Trend Warning Triggered: " + (if .alert_verification.trend_warning_triggered then "✅ YES" else "❌ NO" end) + "\n" +
        "Fast Burn Recovered: " + (if .alert_verification.fast_burn_recovered then "✅ YES" else "❌ NO" end) + "\n" +
        "Slow Burn Recovered: " + (if .alert_verification.slow_burn_recovered then "✅ YES" else "❌ NO" end) + "\n" +
        "Alert System Working: " + (if .validation.alert_system_working then "✅ PASS" else "❌ FAIL" end) + "\n" +
        "Overall Validation: " + (if .validation.all_ok then "✅ PASS" else "❌ PARTIAL" end)
    ' "$output_file"
}

main() {
    echo "=================================================="
    echo "Phase 5-1: SLO Alert Verification"
    echo "=================================================="
    echo
    
    # Prerequisites check
    check_prerequisites
    echo
    
    # Get initial state
    log_phase "Collecting initial alert state..."
    query_alertmanager_alerts
    echo
    
    # Monitor alerts for specified duration
    local detection_results
    detection_results=$(monitor_alerts "$CHECK_DURATION")
    echo
    
    # Final alert state check
    log_phase "Collecting final alert state..."
    query_alertmanager_alerts
    echo
    
    # Generate verification report
    generate_verification_report "$detection_results"
    echo
    
    log_phase "Alert verification completed!"
    log_info "Review results in reports/phase5_slo_alert_verify.json"
    log_info "Next: Combine results with synthetic test data for final validation"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  -h, --help                    Show this help"
        echo "  PROMETHEUS_URL=<url>          Prometheus URL (default: http://localhost:31390)"
        echo "  ALERTMANAGER_URL=<url>        Alertmanager URL (default: http://localhost:31393)"
        echo "  CHECK_DURATION=<sec>          Monitoring duration (default: 300s)"
        echo
        echo "Example:"
        echo "  PROMETHEUS_URL=http://localhost:9090 CHECK_DURATION=600 $0"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac