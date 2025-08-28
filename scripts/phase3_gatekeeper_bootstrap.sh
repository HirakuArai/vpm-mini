#!/usr/bin/env bash
set -euo pipefail

echo "=== Gatekeeper Bootstrap Script ==="
echo "Deploying OPA Gatekeeper and security constraints..."

# Check cluster connectivity
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to cluster"

# Deploy Gatekeeper system
echo ""
echo "📦 Deploying Gatekeeper system..."
kubectl apply -f infra/k8s/base/gatekeeper/system/gatekeeper.yaml

echo ""
echo "⏳ Waiting for Gatekeeper controllers to be ready..."
kubectl -n gatekeeper-system rollout status deployment/gatekeeper-controller-manager --timeout=180s
kubectl -n gatekeeper-system rollout status deployment/gatekeeper-audit --timeout=180s

# Give webhook time to register
echo ""
echo "⏳ Waiting for webhook registration..."
sleep 10

# Deploy ConstraintTemplates
echo ""
echo "📦 Deploying ConstraintTemplates..."
kubectl apply -f infra/k8s/policies/templates/

echo ""
echo "⏳ Waiting for ConstraintTemplates to be established..."
for template in requireserviceaccount requirespiresocket requirenetworkpolicy; do
    echo "  - Waiting for $template..."
    kubectl wait --for=condition=established constrainttemplate/$template --timeout=60s
done

# Deploy NetworkPolicies first (required for NetworkPolicy constraint)
echo ""
echo "📦 Deploying NetworkPolicies..."
kubectl apply -f infra/k8s/policies/networkpolicies/

# Deploy Constraints
echo ""
echo "📦 Deploying Constraints..."
kubectl apply -f infra/k8s/policies/constraints/

echo ""
echo "⏳ Waiting for Constraints to be ready..."
sleep 5

echo ""
echo "✅ Gatekeeper bootstrap complete!"
echo ""
echo "📊 Gatekeeper System Status:"
kubectl -n gatekeeper-system get pods -o wide

echo ""
echo "📋 ConstraintTemplates:"
kubectl get constrainttemplates

echo ""
echo "📋 Constraints:"
kubectl get constraints

echo ""
echo "Run 'bash scripts/phase3_gatekeeper_verify.sh' to verify policy enforcement"