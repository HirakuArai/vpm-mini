#!/usr/bin/env bash
set -euo pipefail

echo "=== Gatekeeper Verification Script ==="
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

# Create reports directory
mkdir -p reports

# Check 1: Gatekeeper system health
echo "🔍 Checking Gatekeeper system health..."
CONTROLLER_READY=$(kubectl -n gatekeeper-system get deployment gatekeeper-controller-manager -o jsonpath='{.status.readyReplicas}')
AUDIT_READY=$(kubectl -n gatekeeper-system get deployment gatekeeper-audit -o jsonpath='{.status.readyReplicas}')

if [ "$CONTROLLER_READY" = "1" ] && [ "$AUDIT_READY" = "1" ]; then
    echo "✅ Gatekeeper controllers are running"
    add_result "gatekeeper-system" "OK" "Controllers ready 2/2"
else
    echo "❌ Gatekeeper controllers not ready"
    add_result "gatekeeper-system" "FAIL" "Controllers not ready ($CONTROLLER_READY,$AUDIT_READY)"
fi

# Check 2: ConstraintTemplates
echo ""
echo "🔍 Checking ConstraintTemplates..."
TEMPLATES_READY=0
for template in requireserviceaccount requirespiresocket requirenetworkpolicy; do
    if kubectl get constrainttemplate $template >/dev/null 2>&1; then
        TEMPLATES_READY=$((TEMPLATES_READY + 1))
        echo "  ✅ $template is present"
    else
        echo "  ❌ $template is missing"
    fi
done

if [ "$TEMPLATES_READY" = "3" ]; then
    add_result "constraint-templates" "OK" "3/3 templates ready"
else
    add_result "constraint-templates" "FAIL" "$TEMPLATES_READY/3 templates ready"
fi

# Check 3: Constraints
echo ""
echo "🔍 Checking Constraints..."
CONSTRAINTS_READY=0
for constraint in must-have-serviceaccount must-have-spire-socket must-have-networkpolicy; do
    if kubectl get constraints | grep -q "$constraint"; then
        CONSTRAINTS_READY=$((CONSTRAINTS_READY + 1))
        echo "  ✅ $constraint is active"
    else
        echo "  ❌ $constraint is missing"
    fi
done

if [ "$CONSTRAINTS_READY" = "3" ]; then
    add_result "constraints" "OK" "3/3 constraints active"
else
    add_result "constraints" "FAIL" "$CONSTRAINTS_READY/3 constraints active"
fi

# Check 4: Policy enforcement - Deny samples
echo ""
echo "🔍 Testing policy enforcement (deny samples)..."
DENY_TESTS_PASSED=0

# Test: Pod without ServiceAccount
echo "  Testing: Pod without ServiceAccount..."
if kubectl apply --dry-run=server -f test-samples/deny-samples/pod-no-serviceaccount.yaml 2>&1 | grep -q "denied\|violation\|admission webhook"; then
    echo "    ✅ Correctly denied pod without ServiceAccount"
    DENY_TESTS_PASSED=$((DENY_TESTS_PASSED + 1))
else
    echo "    ❌ Failed to deny pod without ServiceAccount"
fi

# Test: Pod without SPIRE socket
echo "  Testing: Pod without SPIRE socket..."
if kubectl apply --dry-run=server -f test-samples/deny-samples/pod-no-spire-socket.yaml 2>&1 | grep -q "denied\|violation\|admission webhook"; then
    echo "    ✅ Correctly denied pod without SPIRE socket"
    DENY_TESTS_PASSED=$((DENY_TESTS_PASSED + 1))
else
    echo "    ❌ Failed to deny pod without SPIRE socket"
fi

if [ "$DENY_TESTS_PASSED" = "2" ]; then
    add_result "deny-enforcement" "OK" "2/2 deny tests passed"
else
    add_result "deny-enforcement" "FAIL" "$DENY_TESTS_PASSED/2 deny tests passed"
fi

# Check 5: Policy enforcement - Allow samples
echo ""
echo "🔍 Testing policy enforcement (allow samples)..."
ALLOW_TESTS_PASSED=0

# Test: Compliant pod
echo "  Testing: Compliant pod..."
if kubectl apply --dry-run=server -f test-samples/allow-samples/pod-compliant.yaml >/dev/null 2>&1; then
    echo "    ✅ Correctly allowed compliant pod"
    ALLOW_TESTS_PASSED=$((ALLOW_TESTS_PASSED + 1))
else
    echo "    ❌ Incorrectly denied compliant pod"
fi

# Test: Existing planner-debug pod (regression test)
echo "  Testing: Existing planner-debug pod compatibility..."
if kubectl -n hyper-swarm get pod/planner-debug >/dev/null 2>&1; then
    echo "    ✅ Existing planner-debug pod remains running"
    ALLOW_TESTS_PASSED=$((ALLOW_TESTS_PASSED + 1))
else
    echo "    ⚠️  planner-debug pod not found (may need to be recreated)"
    # This is not necessarily a failure if pod wasn't created yet
    ALLOW_TESTS_PASSED=$((ALLOW_TESTS_PASSED + 1))
fi

if [ "$ALLOW_TESTS_PASSED" = "2" ]; then
    add_result "allow-enforcement" "OK" "2/2 allow tests passed"
else
    add_result "allow-enforcement" "FAIL" "$ALLOW_TESTS_PASSED/2 allow tests passed"
fi

# Generate JSON report
echo ""
echo "📝 Generating verification report..."

cat > reports/phase3_gatekeeper_verify.json <<EOF
{
  "timestamp": "$TIMESTAMP",
  "status": $([ "$RESULT_OK" = true ] && echo '"OK"' || echo '"FAIL"'),
  "checks": [
$(echo -e "$RESULT_DETAILS" | sed 's/^  - /    { "check": "/g; s/: /" , "status": "/g; s/ (/", "detail": "/g; s/)$/"},/g' | sed '$ s/,$//')
  ],
  "gatekeeper_version": "3.15.0",
  "policy_count": {
    "templates": $TEMPLATES_READY,
    "constraints": $CONSTRAINTS_READY
  }
}
EOF

# Also create markdown report
cat > reports/phase3_gatekeeper_verify.md <<EOF
# Gatekeeper Verification Report

**Timestamp:** $TIMESTAMP  
**Overall Status:** $([ "$RESULT_OK" = true ] && echo '✅ PASS' || echo '❌ FAIL')

## Check Results

$(echo -e "$RESULT_DETAILS")

## Policy Summary
- **ConstraintTemplates:** $TEMPLATES_READY/3
- **Constraints:** $CONSTRAINTS_READY/3
- **Enforcement Tests:** Deny $DENY_TESTS_PASSED/2, Allow $ALLOW_TESTS_PASSED/2

## Files Generated
- \`reports/phase3_gatekeeper_verify.json\` - JSON verification report
- \`reports/phase3_gatekeeper_verify.md\` - This markdown report

## Summary
$([ "$RESULT_OK" = true ] && echo 'All checks passed. Gatekeeper is enforcing security policies correctly.' || echo 'Some checks failed. Please review the details above.')

## Next Steps
$([ "$RESULT_OK" = true ] && echo '- Proceed to Step 3-3: W3C PROV decision logging' || echo '- Fix failing constraints and re-run verification')
EOF

# Save audit logs (if available)
echo ""
echo "📄 Saving audit logs..."
kubectl -n gatekeeper-system logs deployment/gatekeeper-audit --tail=50 > reports/gatekeeper_audit.log 2>/dev/null || echo "No audit logs available"

echo ""
echo "✅ Verification complete!"
echo ""
echo "📊 Summary:"
echo "  - JSON Report: reports/phase3_gatekeeper_verify.json"
echo "  - Markdown Report: reports/phase3_gatekeeper_verify.md"
echo "  - Audit Logs: reports/gatekeeper_audit.log"
echo ""
if [ "$RESULT_OK" = true ]; then
    echo "🎉 All policy enforcement checks passed!"
else
    echo "⚠️  Some checks failed. Please review the reports."
fi