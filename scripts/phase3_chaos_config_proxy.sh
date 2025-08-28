#!/bin/bash
set -euo pipefail

# Phase 3-4 Chaos Toxiproxy Configuration Script
# Configure latency injection via Toxiproxy

ADMIN_SVC="toxiproxy"
ADMIN_NS="chaos-engineering"
LISTEN_ADDR="0.0.0.0:8082"
UPSTREAM=""
LATENCY_MS=250
JITTER_MS=50
PROXY_NAME="chaos-proxy"

usage() {
    cat <<EOF
Usage: $0 --upstream UPSTREAM [OPTIONS]

Configure Toxiproxy to inject latency into traffic.

Required:
  --upstream URL            Target upstream service (e.g., http://hello.default.svc.cluster.local)

Options:
  --admin-svc NAME          Toxiproxy admin service name (default: toxiproxy)
  --admin-ns NAMESPACE      Toxiproxy admin namespace (default: chaos-engineering)
  --listen ADDR             Listen address for proxy (default: 0.0.0.0:8082)  
  --latency MS              Base latency in milliseconds (default: 250)
  --jitter MS               Latency jitter in milliseconds (default: 50)
  --proxy-name NAME         Name for the proxy instance (default: chaos-proxy)
  --cleanup                 Remove all proxies and toxics
  -h, --help               Show this help message

Examples:
  $0 --upstream hello.default.svc.cluster.local:80 --latency 300 --jitter 100
  $0 --cleanup

Notes:
  - Requires kubectl port-forward access to Toxiproxy admin API
  - Upstream should be in format: hostname:port (no http://)
  - Proxy will be available at toxiproxy-service:8082 after configuration
EOF
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup_proxies() {
    log "🧹 Cleaning up all Toxiproxy proxies and toxics..."
    
    # List all proxies
    local proxies=$(curl -s http://localhost:8474/proxies | jq -r 'keys[]' 2>/dev/null || true)
    
    if [[ -n "$proxies" ]]; then
        echo "$proxies" | while read -r proxy_name; do
            if [[ -n "$proxy_name" && "$proxy_name" != "null" ]]; then
                log "🗑️  Deleting proxy: $proxy_name"
                curl -s -X DELETE "http://localhost:8474/proxies/$proxy_name" || true
            fi
        done
    else
        log "ℹ️  No proxies found to clean up"
    fi
    
    log "✅ Cleanup completed"
}

# Parse command line arguments
CLEANUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --upstream)
            UPSTREAM="$2"
            shift 2
            ;;
        --admin-svc)
            ADMIN_SVC="$2"
            shift 2
            ;;
        --admin-ns)
            ADMIN_NS="$2"
            shift 2
            ;;
        --listen)
            LISTEN_ADDR="$2"
            shift 2
            ;;
        --latency)
            LATENCY_MS="$2"
            shift 2
            ;;
        --jitter)
            JITTER_MS="$2"
            shift 2
            ;;
        --proxy-name)
            PROXY_NAME="$2"
            shift 2
            ;;
        --cleanup)
            CLEANUP=true
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

log "🔧 Configuring Toxiproxy for latency injection"

# Check if kubectl and required tools are available
for tool in kubectl curl jq; do
    if ! command -v "$tool" &> /dev/null; then
        echo "Error: $tool is required but not installed" >&2
        exit 1
    fi
done

# Verify Toxiproxy service exists
if ! kubectl get svc "$ADMIN_SVC" -n "$ADMIN_NS" > /dev/null 2>&1; then
    echo "Error: Toxiproxy service '$ADMIN_SVC' not found in namespace '$ADMIN_NS'" >&2
    exit 1
fi

# Set up port-forward to Toxiproxy admin API
log "🌐 Setting up port-forward to Toxiproxy admin API..."
kubectl port-forward -n "$ADMIN_NS" "svc/$ADMIN_SVC" 8474:8474 &
PF_PID=$!

# Wait for port-forward to establish
sleep 3

# Cleanup function to kill port-forward on exit
cleanup() {
    if [[ -n "${PF_PID:-}" ]]; then
        kill "$PF_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Test admin API connectivity  
log "🔍 Testing Toxiproxy admin API connectivity..."
if ! curl -f http://localhost:8474/version > /dev/null 2>&1; then
    echo "Error: Cannot connect to Toxiproxy admin API at localhost:8474" >&2
    exit 1
fi

log "✅ Connected to Toxiproxy admin API"

# Handle cleanup mode
if [[ "$CLEANUP" == "true" ]]; then
    cleanup_proxies
    exit 0
fi

# Validate upstream parameter for non-cleanup mode
if [[ -z "$UPSTREAM" ]]; then
    echo "Error: --upstream is required when not using --cleanup" >&2
    usage >&2
    exit 1
fi

log "⚙️  Configuration:"
log "   Proxy name: $PROXY_NAME"
log "   Listen: $LISTEN_ADDR"
log "   Upstream: $UPSTREAM"
log "   Latency: ${LATENCY_MS}ms ± ${JITTER_MS}ms"

# Clean up existing proxy if it exists
if curl -s "http://localhost:8474/proxies/$PROXY_NAME" | jq -e . > /dev/null 2>&1; then
    log "🗑️  Removing existing proxy '$PROXY_NAME'..."
    curl -s -X DELETE "http://localhost:8474/proxies/$PROXY_NAME"
fi

# Create new proxy
log "🔧 Creating proxy '$PROXY_NAME'..."
proxy_config=$(cat <<EOF
{
  "name": "$PROXY_NAME",
  "listen": "$LISTEN_ADDR",
  "upstream": "$UPSTREAM",
  "enabled": true
}
EOF
)

if curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$proxy_config" \
    http://localhost:8474/proxies | jq -e . > /dev/null; then
    log "✅ Proxy '$PROXY_NAME' created successfully"
else
    echo "Error: Failed to create proxy '$PROXY_NAME'" >&2
    exit 1
fi

# Add latency toxic
log "💉 Adding latency toxic (${LATENCY_MS}ms ± ${JITTER_MS}ms)..."
toxic_config=$(cat <<EOF
{
  "name": "latency_downstream",
  "type": "latency",
  "stream": "downstream",
  "toxicity": 1.0,
  "attributes": {
    "latency": $LATENCY_MS,
    "jitter": $JITTER_MS
  }
}
EOF
)

if curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$toxic_config" \
    "http://localhost:8474/proxies/$PROXY_NAME/toxics" | jq -e . > /dev/null; then
    log "✅ Latency toxic added successfully"
else
    echo "Error: Failed to add latency toxic" >&2
    exit 1
fi

# Verify configuration
log "🔍 Verifying proxy configuration..."
proxy_status=$(curl -s "http://localhost:8474/proxies/$PROXY_NAME")
toxics_status=$(curl -s "http://localhost:8474/proxies/$PROXY_NAME/toxics")

echo "$proxy_status" | jq .
echo "Toxics:"
echo "$toxics_status" | jq .

# Generate configuration summary
summary_file="/tmp/toxiproxy_chaos_summary.json"
cat > "$summary_file" <<EOF
{
  "chaos_type": "latency-injection",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "config": {
    "proxy_name": "$PROXY_NAME",
    "listen_address": "$LISTEN_ADDR",
    "upstream": "$UPSTREAM",
    "latency_ms": $LATENCY_MS,
    "jitter_ms": $JITTER_MS,
    "admin_service": "$ADMIN_SVC",
    "admin_namespace": "$ADMIN_NS"
  },
  "proxy_status": $proxy_status,
  "toxics": $toxics_status
}
EOF

log "📋 Configuration summary saved to: $summary_file"

log "🎯 Toxiproxy configuration completed successfully!"
log ""
log "📡 Proxy Details:"
log "   Proxy endpoint: ${ADMIN_SVC}.${ADMIN_NS}.svc.cluster.local:8082"  
log "   Admin API: ${ADMIN_SVC}.${ADMIN_NS}.svc.cluster.local:8474"
log "   Latency injection: ${LATENCY_MS}ms ± ${JITTER_MS}ms"
log ""
log "🧪 To test latency injection:"
log "   kubectl port-forward -n $ADMIN_NS svc/$ADMIN_SVC 8082:8082"
log "   curl http://localhost:8082"
log ""
log "🧹 To cleanup later:"
log "   $0 --cleanup"