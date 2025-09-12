#!/bin/bash
set -euo pipefail

echo "=== 0) 自動検出フェーズ ==============================="

# a) APP_NS の自動検出（hello-ai の ksvc を全NS走査）
APP_NS_DETECTED="$(
  kubectl get ksvc --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{"\n"}{end}' 2>/dev/null \
    | awk '$2=="hello-ai"{print $1; found=1} END{if(!found) exit 1}'
)" || true

# 代替: Deployment/Pod のラベル app=hello-ai でも探索
if [ -z "${APP_NS_DETECTED:-}" ]; then
  APP_NS_DETECTED="$(
    kubectl get pods --all-namespaces -l app=hello-ai -o jsonpath='{range .items[*]}{.metadata.namespace}{"\n"}{end}' 2>/dev/null \
      | head -n1
  )" || true
fi

# b) PROM_RELEASE の自動検出（monitoring NS の Prometheus/Grafana系Podの release ラベル）
PROM_RELEASE_DETECTED="$(
  kubectl -n monitoring get pods -o jsonpath='{range .items[*]}{.metadata.labels.release}{"\n"}{end}' 2>/dev/null \
    | grep -E '^[A-Za-z0-9._-]+' | head -n1
)" || true

# c) 検出結果の採用（ユーザが環境変数を渡している場合は尊重）
APP_NS="${APP_NS:-${APP_NS_DETECTED:-}}"
PROM_RELEASE="${PROM_RELEASE:-${PROM_RELEASE_DETECTED:-}}"

echo "Detected APP_NS       : ${APP_NS:-<not found>}"
echo "Detected PROM_RELEASE : ${PROM_RELEASE:-<not found>}"

# どちらか欠けていたら安全のため中断（誤適用を防止）
if [ -z "${APP_NS:-}" ] || [ -z "${PROM_RELEASE:-}" ]; then
  echo "❌ 必要な値を自動検出できませんでした。次を確認してください："
  echo "  - hello-ai の ksvc もしくは Pod が存在するか（app=hello-ai）"
  echo "  - kube-prometheus-stack が monitoring NS にあり、Pod に 'release' ラベルが付いているか"
  echo "必要なら、以下のように明示指定して再実行できます："
  echo "  APP_NS=<your-ns> PROM_RELEASE=<your-release> bash this_script.sh"
  exit 1
fi

echo "✅ 値を確定しました。APP_NS=${APP_NS}, PROM_RELEASE=${PROM_RELEASE}"

echo "=== 1) Kustomize スキャフォールド整備（冪等） ========"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

APP_BASE="infra/k8s/overlays/dev/hello-ai"
MON_BASE="infra/k8s/overlays/dev/monitoring"
mkdir -p "infra/k8s/overlays/dev" "$APP_BASE" "$MON_BASE"

# hello-ai ksvc（既存があれば再利用、なければ作成）
KSVC_FILE="$APP_BASE/ksvc.yaml"
if [ ! -f "$KSVC_FILE" ]; then
  cat > "$KSVC_FILE" <<YAML
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello-ai
  namespace: ${APP_NS}
spec:
  template:
    metadata:
      labels:
        app: hello-ai
    spec:
      containers:
      - image: ghcr.io/hirakuarai/vpm-mini/hello-ai:latest
        ports:
        - containerPort: 8080
          name: http1
YAML
fi

# metrics Service（port 9090 を公開）
SVC_FILE="$APP_BASE/svc-metrics.yaml"
cat > "$SVC_FILE" <<YAML
apiVersion: v1
kind: Service
metadata:
  name: hello-ai-metrics
  namespace: ${APP_NS}
  labels:
    app: hello-ai
spec:
  selector:
    app: hello-ai
  ports:
  - name: http-metrics
    port: 9090
    targetPort: 8080
    protocol: TCP
YAML

# app 側 kustomization（存在するリソースだけ利用）
cat > "$APP_BASE/kustomization.yaml" <<YAML
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: ${APP_NS}
resources:
  - ksvc.yaml
  - svc-metrics.yaml
YAML

# ServiceMonitor（監視側は monitoring NS で管理）
SM_FILE="$APP_BASE/servicemonitor.yaml"
cat > "$SM_FILE" <<YAML
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: hello-ai
  namespace: monitoring
  labels:
    release: ${PROM_RELEASE}
spec:
  namespaceSelector:
    matchNames: 
    - ${APP_NS}
  selector:
    matchLabels:
      app: hello-ai
  endpoints:
  - port: http-metrics
    interval: 15s
    scrapeTimeout: 10s
    path: /metrics
YAML

# monitoring 側 kustomization（ServiceMonitor と Grafana CM）
cat > "$MON_BASE/kustomization.yaml" <<YAML
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: monitoring
resources:
  - servicemonitor.yaml
  - grafana-dashboard-hello-ai.yaml
YAML

# ServiceMonitor を monitoring ディレクトリにコピー
cp "$SM_FILE" "$MON_BASE/servicemonitor.yaml"

# Grafana ダッシュボード ConfigMap（ダッシュボードJSONが存在すれば投入）
DASH_JSON="dashboards/hello_ai_metrics.json"
GRAF_CM="$MON_BASE/grafana-dashboard-hello-ai.yaml"

if [ -f "$DASH_JSON" ]; then
  # JSONファイルを読み込んでConfigMapに埋め込み
  DASH_CONTENT="$(cat "$DASH_JSON")"
  cat > "$GRAF_CM" <<YAML
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-hello-ai
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  hello_ai_metrics.json: |
$(echo "${DASH_CONTENT}" | sed 's/^/    /')
YAML
else
  # デフォルトのダッシュボード
  cat > "$GRAF_CM" <<'YAML'
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-hello-ai
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  hello_ai_metrics.json: |
    {
      "title": "Hello AI Metrics",
      "panels": [
        {
          "title": "Request Rate",
          "targets": [
            {
              "expr": "rate(http_requests_total{job=\"hello-ai\"}[5m])"
            }
          ]
        },
        {
          "title": "Request Duration",
          "targets": [
            {
              "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"hello-ai\"}[5m]))"
            }
          ]
        }
      ],
      "refresh": "10s",
      "time": {
        "from": "now-1h",
        "to": "now"
      }
    }
YAML
fi

echo "=== 2) 適用（kubectl apply -k 使用） =================="

# hello-ai リソースを適用
echo "Applying hello-ai resources..."
kubectl apply -k "$APP_BASE"

# monitoring リソースを適用
echo "Applying monitoring resources..."
kubectl apply -k "$MON_BASE"

echo "=== 3) 即時検証 ======================================"

echo "[A] hello-ai resources in namespace ${APP_NS}"
kubectl -n "${APP_NS}" get ksvc hello-ai --no-headers 2>/dev/null || echo "  ksvc not found"
kubectl -n "${APP_NS}" get svc hello-ai-metrics --no-headers 2>/dev/null || echo "  metrics service not found"

echo ""
echo "[B] Metrics Service details"
kubectl -n "${APP_NS}" get svc hello-ai-metrics -o yaml 2>/dev/null | grep -E 'name: http-metrics|port: 9090|app: hello-ai' || true

echo ""
echo "[C] Test /metrics endpoint via port-forward"
# Start port-forward in background
(kubectl -n "${APP_NS}" port-forward svc/hello-ai-metrics 19090:9090 >/dev/null 2>&1 & echo $! > /tmp/pf_hello.pid) 2>/dev/null
sleep 2

# Test metrics endpoint
if curl -s --connect-timeout 2 localhost:19090/metrics 2>/dev/null | head -5; then
  echo "  ✅ Metrics endpoint is accessible"
else
  echo "  ⚠️ Could not access metrics endpoint"
fi

# Clean up port-forward
[ -f /tmp/pf_hello.pid ] && kill $(cat /tmp/pf_hello.pid) 2>/dev/null || true
rm -f /tmp/pf_hello.pid

echo ""
echo "[D] ServiceMonitor in monitoring namespace"
kubectl -n monitoring get servicemonitor hello-ai -o yaml 2>/dev/null | grep -E 'release:|matchNames:' || echo "  ServiceMonitor not found"

echo ""
echo "[E] Prometheus target discovery"
# Find Prometheus service
PROM_SVC="$(kubectl -n monitoring get svc -o name 2>/dev/null | grep -E 'prometheus' | grep -v alertmanager | head -n1 | cut -d/ -f2)"

if [ -n "${PROM_SVC:-}" ]; then
  echo "  Found Prometheus service: ${PROM_SVC}"
  
  # Port-forward to Prometheus
  (kubectl -n monitoring port-forward svc/${PROM_SVC} 19091:9090 >/dev/null 2>&1 & echo $! > /tmp/pf_prom.pid) 2>/dev/null
  sleep 2
  
  # Check targets
  if curl -s --connect-timeout 2 "http://localhost:19091/api/v1/targets" 2>/dev/null | jq -r '.data.activeTargets[] | select(.labels.job == "hello-ai" or .labels.job == "serviceMonitor/monitoring/hello-ai") | "  Target: \(.labels.job) - Health: \(.health)"' 2>/dev/null; then
    echo "  ✅ hello-ai target found in Prometheus"
  else
    echo "  ⚠️ hello-ai target not yet discovered by Prometheus"
  fi
  
  # Clean up
  [ -f /tmp/pf_prom.pid ] && kill $(cat /tmp/pf_prom.pid) 2>/dev/null || true
  rm -f /tmp/pf_prom.pid
else
  echo "  ⚠️ Prometheus service not found in monitoring namespace"
fi

echo ""
echo "[F] Grafana dashboard ConfigMap"
kubectl -n monitoring get cm grafana-dashboard-hello-ai --no-headers 2>/dev/null && echo "  ✅ Dashboard ConfigMap exists" || echo "  ⚠️ Dashboard ConfigMap not found"

echo ""
echo "=== 4) Git commit and tag (optional) =================="

# Check if there are changes to commit
if git diff --quiet && git diff --cached --quiet; then
  echo "No changes to commit"
else
  echo "Committing changes..."
  git add -A
  git commit -m "feat(p4): auto-setup metrics monitoring for hello-ai

- Auto-detected APP_NS=${APP_NS}
- Auto-detected PROM_RELEASE=${PROM_RELEASE}
- Created kustomize overlays for dev environment
- Applied ServiceMonitor and Grafana dashboard
- Verified metrics endpoint and Prometheus discovery"

  # Create tag
  TAG="p4-metrics-auto-$(date +%Y%m%d_%H%M%S)"
  git tag -a "${TAG}" -m "P4 metrics auto-setup complete (APP_NS=${APP_NS}, PROM_RELEASE=${PROM_RELEASE})"
  echo "Created tag: ${TAG}"
fi

echo ""
echo "========================================================="
echo "✅ Setup completed successfully!"
echo "  - Namespace: ${APP_NS}"
echo "  - Prometheus Release: ${PROM_RELEASE}"
echo "  - Metrics endpoint: http://hello-ai-metrics.${APP_NS}:9090/metrics"
echo "  - ServiceMonitor: monitoring/hello-ai"
echo "  - Grafana dashboard: monitoring/grafana-dashboard-hello-ai"
echo "========================================================="