#!/usr/bin/env bash
set -euo pipefail

echo "=== SPIRE Bootstrap Script ==="
echo "Deploying SPIRE components to Kubernetes cluster..."

# Check cluster connectivity
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to cluster"

# Apply SPIRE base manifests
echo ""
echo "📦 Applying SPIRE base manifests..."
kubectl apply -f infra/k8s/base/spire/namespace.yaml
kubectl apply -f infra/k8s/base/spire/rbac.yaml
kubectl apply -f infra/k8s/base/spire/bundle-configmap.yaml
kubectl apply -f infra/k8s/base/spire/server-configmap.yaml
kubectl apply -f infra/k8s/base/spire/server-statefulset.yaml
kubectl apply -f infra/k8s/base/spire/server-service.yaml
kubectl apply -f infra/k8s/base/spire/agent-configmap.yaml
kubectl apply -f infra/k8s/base/spire/agent-daemonset.yaml
kubectl apply -f infra/k8s/base/spire/workload-registrar-configmap.yaml
kubectl apply -f infra/k8s/base/spire/workload-registrar-deployment.yaml

echo ""
echo "⏳ Waiting for SPIRE Server to be ready..."
kubectl -n spire-system rollout status statefulset/spire-server --timeout=180s

echo ""
echo "⏳ Waiting for SPIRE Agent to be ready..."
kubectl -n spire-system rollout status daemonset/spire-agent --timeout=180s

echo ""
echo "⏳ Waiting for Workload Registrar to be ready..."
kubectl -n spire-system rollout status deployment/spire-k8s-workload-registrar --timeout=180s

echo ""
echo "📦 Applying test workloads..."
kubectl apply -f infra/k8s/overlays/dev/examples/namespace.yaml
kubectl apply -f infra/k8s/overlays/dev/examples/planner-test-sa.yaml
kubectl apply -f infra/k8s/overlays/dev/examples/planner-test-pod.yaml

echo ""
echo "⏳ Waiting for test pod to be ready..."
kubectl -n hyper-swarm wait pod/planner-debug --for=condition=ready --timeout=60s || true

echo ""
echo "✅ SPIRE bootstrap complete!"
echo ""
echo "📊 SPIRE System Status:"
kubectl -n spire-system get pods -o wide

echo ""
echo "🧪 Test Workload Status:"
kubectl -n hyper-swarm get pods -o wide

echo ""
echo "Run 'bash scripts/phase3_spire_verify.sh' to verify SPIRE setup"