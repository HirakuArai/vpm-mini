#!/bin/bash
set -euo pipefail

# Phase 3-4 Chaos Bootstrap
# Deploy chaos engineering infrastructure and verify dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔥 Bootstrapping Chaos Engineering for Phase 3-4..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not installed"
    exit 1
fi

# Install Python dependencies for chaos scripts
echo "📦 Installing Python dependencies for chaos engineering..."
pip3 install aiohttp requests prometheus-client

# Deploy Toxiproxy
echo "☠️  Deploying Toxiproxy chaos proxy..."
kubectl apply -f "$PROJECT_ROOT/infra/k8s/base/chaos/toxiproxy.yaml"

# Wait for Toxiproxy to be ready
echo "⏳ Waiting for Toxiproxy to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/toxiproxy -n chaos-engineering

# Verify Toxiproxy is responding
echo "🔍 Verifying Toxiproxy admin API..."
kubectl port-forward -n chaos-engineering svc/toxiproxy 8474:8474 &
TOXIPROXY_PF_PID=$!
sleep 5

# Test admin API
if curl -f http://localhost:8474/version > /dev/null 2>&1; then
    echo "✅ Toxiproxy admin API is responding"
else
    echo "❌ Toxiproxy admin API is not responding"
    kill $TOXIPROXY_PF_PID 2>/dev/null || true
    exit 1
fi

# Clean up port-forward
kill $TOXIPROXY_PF_PID 2>/dev/null || true

# Check if target service exists
echo "🎯 Checking target service (hello)..."
if kubectl get ksvc hello -n default > /dev/null 2>&1; then
    echo "✅ Target service 'hello' found in default namespace"
    TARGET_URL=$(kubectl get ksvc hello -n default -o jsonpath='{.status.url}')
    echo "   URL: $TARGET_URL"
else
    echo "⚠️  Target service 'hello' not found. Creating simple test service..."
    
    # Create a minimal test service if needed
    cat <<EOF | kubectl apply -f -
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/target: "100"
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
      - image: gcr.io/knative-samples/helloworld-go
        ports:
        - containerPort: 8080
        env:
        - name: TARGET
          value: "Chaos Test"
EOF
    
    echo "⏳ Waiting for test service to be ready..."
    kubectl wait --for=condition=Ready --timeout=120s ksvc/hello -n default
    TARGET_URL=$(kubectl get ksvc hello -n default -o jsonpath='{.status.url}')
    echo "✅ Test service created: $TARGET_URL"
fi

# Check Prometheus (should be available from Phase 2)
echo "📊 Checking Prometheus availability..."
if kubectl get svc prometheus-server -n prometheus > /dev/null 2>&1; then
    echo "✅ Prometheus found in prometheus namespace"
elif kubectl get svc prometheus -n monitoring > /dev/null 2>&1; then
    echo "✅ Prometheus found in monitoring namespace"  
else
    echo "⚠️  Prometheus not found. Chaos verification will use mock data."
fi

echo ""
echo "🎉 Chaos engineering bootstrap completed successfully!"
echo ""
echo "📋 Summary:"
echo "  ✅ Toxiproxy deployed and running"
echo "  ✅ Target service available: $TARGET_URL"
echo "  ✅ Dependencies installed"
echo ""
echo "🔧 Next steps:"
echo "  1. Run pod-kill scenario: bash scripts/phase3_chaos_podkill.sh"
echo "  2. Run latency scenario: bash scripts/phase3_chaos_config_proxy.sh"
echo "  3. Generate load: python3 scripts/phase3_chaos_loadgen.py"
echo "  4. Verify SLOs: python3 scripts/phase3_chaos_verify.py"
echo ""