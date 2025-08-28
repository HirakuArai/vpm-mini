#!/usr/bin/env bash
set -euo pipefail

# Phase 4-1: Istio + Gateway API Verification Script
# Tests /hello route via Istio Gateway and measures p50 latency

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default parameters
PATH_TO_TEST="/hello"
REQUEST_COUNT=30
TIMEOUT=2
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            PATH_TO_TEST="$2"
            shift 2
            ;;
        --count)
            REQUEST_COUNT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --path PATH     Path to test (default: /hello)"
            echo "  --count COUNT   Number of requests (default: 30)"
            echo "  --timeout SEC   Request timeout (default: 2)"
            echo "  --verbose       Enable verbose output"
            echo "  --help          Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "Phase 4-1: Istio Gateway Verification"
echo "========================================="
echo "Path: ${PATH_TO_TEST}"
echo "Count: ${REQUEST_COUNT}"
echo "Timeout: ${TIMEOUT}s"
echo "========================================="

# Create reports directory
mkdir -p "${PROJECT_ROOT}/reports"

# Initialize results
REACHABLE=false
LATENCIES=()
SUCCESS_COUNT=0
ERROR_COUNT=0

# Get Istio ingress gateway NodePort
log_info "Getting Istio ingress gateway NodePort..."
NODEPORT=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}' 2>/dev/null || echo "")

if [[ -z "$NODEPORT" ]]; then
    log_error "Failed to get Istio ingress gateway NodePort"
    log_error "Is Istio installed and istio-ingressgateway service available?"
    exit 1
fi

log_info "Istio ingress gateway NodePort: ${NODEPORT}"

# Get kind cluster IP (for kind, this is usually localhost or 127.0.0.1)
CLUSTER_IP="localhost"
BASE_URL="http://${CLUSTER_IP}:${NODEPORT}"

log_info "Testing URL: ${BASE_URL}${PATH_TO_TEST}"

# Check if hello service exists
log_info "Checking if hello service is available..."
if ! kubectl get ksvc hello -n hyper-swarm >/dev/null 2>&1; then
    log_warn "hello Knative service not found in hyper-swarm namespace"
    log_warn "Please ensure hello service is deployed before testing"
fi

# Wait a bit for Gateway/HTTPRoute to be ready
log_info "Waiting for Gateway/HTTPRoute to be ready..."
sleep 5

# Perform requests and measure latencies
log_info "Performing ${REQUEST_COUNT} requests..."

for i in $(seq 1 $REQUEST_COUNT); do
    if [[ "$VERBOSE" == "true" ]]; then
        echo -n "Request $i/$REQUEST_COUNT: "
    fi
    
    # Measure request time
    START_TIME=$(date +%s%N)
    
    # Make HTTP request with Host header
    HTTP_CODE=$(curl -w "%{http_code}" -s -o /dev/null \
        --connect-timeout "$TIMEOUT" \
        --max-time "$TIMEOUT" \
        -H "Host: hello.hyper-swarm.svc.cluster.local" \
        "${BASE_URL}${PATH_TO_TEST}" 2>/dev/null || echo "000")
    
    END_TIME=$(date +%s%N)
    LATENCY_NS=$((END_TIME - START_TIME))
    LATENCY_MS=$((LATENCY_NS / 1000000))
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        LATENCIES+=("$LATENCY_MS")
        REACHABLE=true
        
        if [[ "$VERBOSE" == "true" ]]; then
            echo "OK (${LATENCY_MS}ms)"
        fi
    else
        ERROR_COUNT=$((ERROR_COUNT + 1))
        
        if [[ "$VERBOSE" == "true" ]]; then
            echo "FAIL (HTTP $HTTP_CODE)"
        fi
    fi
    
    # Brief pause between requests
    sleep 0.1
done

# Calculate statistics
TOTAL_REQUESTS=$((SUCCESS_COUNT + ERROR_COUNT))
SUCCESS_RATE=$(( (SUCCESS_COUNT * 100) / TOTAL_REQUESTS ))

# Calculate p50 latency (median)
P50_MS=0
if [[ ${#LATENCIES[@]} -gt 0 ]]; then
    # Sort latencies
    IFS=$'\n' SORTED_LATENCIES=($(sort -n <<<"${LATENCIES[*]}"))
    unset IFS
    
    # Calculate median (p50)
    LATENCY_COUNT=${#SORTED_LATENCIES[@]}
    if [[ $((LATENCY_COUNT % 2)) -eq 0 ]]; then
        # Even number of elements
        IDX1=$((LATENCY_COUNT / 2 - 1))
        IDX2=$((LATENCY_COUNT / 2))
        P50_MS=$(( (SORTED_LATENCIES[IDX1] + SORTED_LATENCIES[IDX2]) / 2 ))
    else
        # Odd number of elements
        IDX=$((LATENCY_COUNT / 2))
        P50_MS=${SORTED_LATENCIES[IDX]}
    fi
fi

# Display results
echo ""
echo "========================================="
echo "Verification Results"
echo "========================================="

log_info "Total requests: ${TOTAL_REQUESTS}"
log_info "Successful requests: ${SUCCESS_COUNT}"
log_info "Failed requests: ${ERROR_COUNT}"
log_info "Success rate: ${SUCCESS_RATE}%"
log_info "P50 latency: ${P50_MS}ms"

# Generate JSON result
RESULT_JSON="${PROJECT_ROOT}/reports/phase4_istio_verify.json"
cat > "$RESULT_JSON" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "commit": "$(git rev-parse --short HEAD)",
  "branch": "$(git branch --show-current)",
  "test_config": {
    "path": "$PATH_TO_TEST",
    "count": $REQUEST_COUNT,
    "timeout": $TIMEOUT
  },
  "results": {
    "reachable": $REACHABLE,
    "total_requests": $TOTAL_REQUESTS,
    "successful_requests": $SUCCESS_COUNT,
    "failed_requests": $ERROR_COUNT,
    "success_rate_percent": $SUCCESS_RATE,
    "p50_ms": $P50_MS
  },
  "istio_config": {
    "gateway_nodeport": $NODEPORT,
    "base_url": "$BASE_URL"
  }
}
EOF

log_info "Results saved to: $RESULT_JSON"

# Check if verification passes
PASS=true
if [[ "$REACHABLE" != "true" ]]; then
    log_error "❌ Hello service not reachable via Istio Gateway"
    PASS=false
fi

if [[ $SUCCESS_RATE -lt 90 ]]; then
    log_warn "⚠️  Success rate below 90%: ${SUCCESS_RATE}%"
fi

if [[ $P50_MS -gt 1000 ]]; then
    log_warn "⚠️  P50 latency above 1000ms: ${P50_MS}ms"
fi

echo ""
if [[ "$PASS" == "true" ]]; then
    log_info "✅ Phase 4-1 Istio Gateway verification PASSED"
    log_info "   - Hello service reachable via Istio Gateway"
    log_info "   - P50 latency: ${P50_MS}ms"
    log_info "   - Success rate: ${SUCCESS_RATE}%"
    exit 0
else
    log_error "❌ Phase 4-1 Istio Gateway verification FAILED"
    log_error "   Please check Istio installation and hello service deployment"
    exit 1
fi