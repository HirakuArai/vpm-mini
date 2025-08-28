#!/usr/bin/env bash
set -euo pipefail

echo "=== SPIRE Verification Script ==="
echo ""

# Initialize result tracking
RESULT_OK=true
RESULT_DETAILS=""
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Function to add result detail
add_result() {
    local check="$1"
    local status="$2"
    local detail="$3"
    RESULT_DETAILS="${RESULT_DETAILS}  - ${check}: ${status} (${detail})\n"
    if [ "$status" != "OK" ]; then
        RESULT_OK=false
    fi
}

# Check 1: SPIRE Server health
echo "🔍 Checking SPIRE Server health..."
if kubectl -n spire-system get statefulset spire-server -o jsonpath='{.status.readyReplicas}' | grep -q '1'; then
    SERVER_LOG=$(kubectl -n spire-system logs statefulset/spire-server --tail=5 2>&1 | grep -E "(INFO|DEBUG)" | tail -1 || echo "No logs")
    echo "✅ SPIRE Server is running"
    add_result "spire-server" "OK" "Ready 1/1"
else
    echo "❌ SPIRE Server is not ready"
    add_result "spire-server" "FAIL" "Not ready"
fi

# Check 2: SPIRE Agent health
echo ""
echo "🔍 Checking SPIRE Agent health..."
AGENT_DESIRED=$(kubectl -n spire-system get daemonset spire-agent -o jsonpath='{.status.desiredNumberScheduled}')
AGENT_READY=$(kubectl -n spire-system get daemonset spire-agent -o jsonpath='{.status.numberReady}')
if [ "$AGENT_DESIRED" = "$AGENT_READY" ] && [ "$AGENT_READY" -gt 0 ]; then
    echo "✅ SPIRE Agent DaemonSet is running ($AGENT_READY/$AGENT_DESIRED)"
    add_result "spire-agent" "OK" "Ready $AGENT_READY/$AGENT_DESIRED"
else
    echo "❌ SPIRE Agent DaemonSet is not ready ($AGENT_READY/$AGENT_DESIRED)"
    add_result "spire-agent" "FAIL" "Not ready $AGENT_READY/$AGENT_DESIRED"
fi

# Check 3: Workload Registrar health
echo ""
echo "🔍 Checking Workload Registrar health..."
if kubectl -n spire-system get deployment spire-k8s-workload-registrar -o jsonpath='{.status.readyReplicas}' | grep -q '1'; then
    echo "✅ Workload Registrar is running"
    add_result "workload-registrar" "OK" "Ready 1/1"
else
    echo "❌ Workload Registrar is not ready"
    add_result "workload-registrar" "FAIL" "Not ready"
fi

# Check 4: Workload entries
echo ""
echo "🔍 Checking registered workload entries..."
echo ""
# Create entry show command
ENTRY_CMD="/opt/spire/bin/spire-server entry show"
ENTRIES=$(kubectl -n spire-system exec statefulset/spire-server -- $ENTRY_CMD 2>/dev/null || echo "")
echo "$ENTRIES" > reports/spire_entries.txt

# Check for planner-sa entry
if echo "$ENTRIES" | grep -q "spiffe://vpm-mini.local/ns/hyper-swarm/sa/planner-sa"; then
    echo "✅ Found SPIFFE ID for planner-sa"
    add_result "workload-entry-planner" "OK" "spiffe://vpm-mini.local/ns/hyper-swarm/sa/planner-sa"
    
    # Display the entry details
    echo ""
    echo "📋 Planner SA Entry Details:"
    echo "$ENTRIES" | grep -A 5 "spiffe://vpm-mini.local/ns/hyper-swarm/sa/planner-sa" | head -10
else
    echo "❌ No SPIFFE ID found for planner-sa"
    add_result "workload-entry-planner" "FAIL" "No entry found"
fi

# Check 5: Socket mount in test pod
echo ""
echo "🔍 Checking SPIRE socket mount in test pod..."
SOCKET_CHECK=$(kubectl -n hyper-swarm exec pod/planner-debug -- ls -la /run/spire/sockets/ 2>/dev/null || echo "Socket directory not found")
echo "$SOCKET_CHECK" > reports/spire_socket_check.txt

if echo "$SOCKET_CHECK" | grep -q "agent.sock"; then
    echo "✅ SPIRE agent socket is mounted in test pod"
    add_result "socket-mount" "OK" "/run/spire/sockets/agent.sock exists"
    echo ""
    echo "📋 Socket Details:"
    echo "$SOCKET_CHECK"
else
    echo "❌ SPIRE agent socket not found in test pod"
    add_result "socket-mount" "FAIL" "Socket not found"
fi

# Generate JSON report
echo ""
echo "📝 Generating verification report..."
mkdir -p reports

cat > reports/phase3_spire_verify.json <<EOF
{
  "timestamp": "$TIMESTAMP",
  "status": $([ "$RESULT_OK" = true ] && echo '"OK"' || echo '"FAIL"'),
  "checks": [
$(echo -e "$RESULT_DETAILS" | sed 's/^  - /    { "check": "/g; s/: /" , "status": "/g; s/ (/", "detail": "/g; s/)$/"},/g' | sed '$ s/,$//')
  ],
  "entries_file": "reports/spire_entries.txt",
  "socket_check_file": "reports/spire_socket_check.txt"
}
EOF

# Also create markdown report
cat > reports/phase3_spire_verify.md <<EOF
# SPIRE Verification Report

**Timestamp:** $TIMESTAMP  
**Overall Status:** $([ "$RESULT_OK" = true ] && echo '✅ PASS' || echo '❌ FAIL')

## Check Results

$(echo -e "$RESULT_DETAILS")

## Files Generated
- \`reports/spire_entries.txt\` - Full SPIRE entry list
- \`reports/spire_socket_check.txt\` - Socket mount verification
- \`reports/phase3_spire_verify.json\` - JSON verification report

## Summary
$([ "$RESULT_OK" = true ] && echo 'All checks passed. SPIRE is ready for workload identity management.' || echo 'Some checks failed. Please review the details above.')
EOF

echo ""
echo "✅ Verification complete!"
echo ""
echo "📊 Summary:"
echo "  - JSON Report: reports/phase3_spire_verify.json"
echo "  - Markdown Report: reports/phase3_spire_verify.md"
echo "  - Entry List: reports/spire_entries.txt"
echo "  - Socket Check: reports/spire_socket_check.txt"
echo ""
if [ "$RESULT_OK" = true ]; then
    echo "🎉 All checks passed! SPIRE is operational."
else
    echo "⚠️  Some checks failed. Please review the reports."
fi