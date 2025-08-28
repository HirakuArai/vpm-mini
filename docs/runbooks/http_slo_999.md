# HTTP SLO 99.9% Incident Response Runbook

## Alert Summary
- **SLO Target**: 99.9% success rate for HTTP requests to hello service
- **Service**: hello (Knative Service in hyper-swarm namespace)
- **Error Budget**: 0.1% monthly (43.2 minutes downtime per month)
- **Monitoring**: Istio service mesh metrics via Prometheus

## Alert Types

### 🚨 SLOFastBurn (severity: page)
- **Threshold**: 14.4x error budget burn rate over 5 minutes
- **Impact**: Will exhaust monthly error budget in ~2 hours
- **Response Time**: Immediate (< 5 minutes)

### ⚠️ SLOSlowBurn (severity: ticket)  
- **Threshold**: 6x error budget burn rate over 30 minutes
- **Impact**: Will exhaust monthly error budget in ~5 days
- **Response Time**: Within 30 minutes

### 📈 SLOErrorBudgetLow (severity: warning)
- **Threshold**: 3x error budget burn rate over 1 hour
- **Impact**: Trending toward SLO breach
- **Response Time**: Within 1 hour

## Immediate Response (Fast Burn)

### 1. 症状確認 (Symptom Verification)
```bash
# Check current error rate
kubectl exec -n monitoring deployment/prometheus -- \
  promtool query instant 'sli:http_error_rate:5m{service="hello"}'

# Check alert status
kubectl exec -n monitoring deployment/prometheus -- \
  promtool query instant 'ALERTS{alertname="SLOFastBurn"}'

# Verify service health
kubectl -n hyper-swarm get ksvc hello
kubectl -n hyper-swarm get pods -l serving.knative.dev/service=hello
```

### 2. 即時対処 (Immediate Mitigation)

#### Option A: Traffic Reduction
```bash
# Emergency traffic reduction via HTTPRoute weight adjustment
kubectl -n hyper-swarm patch httproute hello-route --type merge -p '{
  "spec": {"rules": [{"backendRefs": [
    {"kind":"Service","name":"hello","port":80,"weight": 50},
    {"kind":"Service","name":"hello-v2","port":80,"weight": 50}
  ]}]}
}'
```

#### Option B: Rollback to Previous Version
```bash
# Rollback to 100% stable version (hello)
kubectl -n hyper-swarm patch httproute hello-route --type merge -p '{
  "spec": {"rules": [{"backendRefs": [
    {"kind":"Service","name":"hello","port":80,"weight": 100},
    {"kind":"Service","name":"hello-v2","port":80,"weight": 0}
  ]}]}
}'
```

#### Option C: Scale Up Resources
```bash
# Force scale-up of hello service
kubectl -n hyper-swarm annotate ksvc hello \
  autoscaling.knative.dev/minScale=5

# Check scaling status
watch kubectl -n hyper-swarm get pods -l serving.knative.dev/service=hello
```

### 3. 状況監視 (Monitor Recovery)
```bash
# Monitor error rate recovery
watch kubectl exec -n monitoring deployment/prometheus -- \
  promtool query instant 'sli:http_error_rate:5m{service="hello"}'

# Monitor alert resolution
watch kubectl exec -n monitoring deployment/prometheus -- \
  promtool query instant 'ALERTS{alertname="SLOFastBurn",alertstate="firing"}'
```

## Root Cause Analysis

### 4. 原因切り分け (Root Cause Investigation)

#### Service-Level Issues
```bash
# Check service logs
kubectl -n hyper-swarm logs -l serving.knative.dev/service=hello --tail=100

# Check resource utilization  
kubectl -n hyper-swarm top pods -l serving.knative.dev/service=hello

# Check service configuration
kubectl -n hyper-swarm get ksvc hello -o yaml
```

#### Infrastructure-Level Issues
```bash
# Check node health
kubectl get nodes
kubectl describe nodes

# Check cluster resource usage
kubectl top nodes

# Check istio-proxy sidecar logs
kubectl -n hyper-swarm logs -l serving.knative.dev/service=hello -c istio-proxy --tail=50
```

#### Network-Level Issues  
```bash
# Check NetworkPolicy blocking traffic
kubectl -n hyper-swarm get networkpolicies

# Check Gateway and HTTPRoute configuration
kubectl -n hyper-swarm get gateway vpm-mini-gateway -o yaml
kubectl -n hyper-swarm get httproute hello-route -o yaml

# Check service discovery
kubectl -n hyper-swarm get endpoints hello hello-v2
```

#### Upstream Dependencies
```bash
# Check Redis connectivity (if applicable)
kubectl -n hyper-swarm exec deployment/redis -- redis-cli ping

# Check external service health
curl -fsS http://localhost:31380/hello
```

## Metrics & Logs Reference

### Key Prometheus Queries
```promql
# Current error rate (5m window)
sli:http_error_rate:5m{service="hello"}

# Success rate trend
sli:http_success_rate:30m{service="hello"}  

# Request rate
sum(rate(istio_requests_total{destination_workload="hello"}[5m]))

# Latency percentiles
histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{destination_workload="hello"}[5m])) by (le))
histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{destination_workload="hello"}[5m])) by (le))

# Error budget consumption
sli:http_error_rate:5m{service="hello"} / sli:http_error_budget{service="hello"}
```

### Grafana Dashboards
- **Service Overview**: http://localhost:3000/d/service-overview
- **SLO Dashboard**: http://localhost:3000/d/slo-monitoring  
- **Istio Metrics**: http://localhost:3000/d/istio-service-mesh
- **Knative Serving**: http://localhost:3000/d/knative-serving

### Log Aggregation
```bash
# Service logs with trace correlation
kubectl -n hyper-swarm logs -l serving.knative.dev/service=hello \
  --since=15m | grep ERROR

# Istio access logs
kubectl -n hyper-swarm logs -l serving.knative.dev/service=hello \
  -c istio-proxy --since=15m | jq 'select(.response_code >= 400)'
```

## Long-term Resolution

### 5. 恒久対策 (Permanent Fix)

#### Code-Level Fixes
- Review application error handling and timeout configurations
- Implement circuit breakers and retry mechanisms  
- Add graceful degradation for dependency failures
- Optimize database queries and external API calls

#### Infrastructure Improvements
- Implement auto-scaling based on custom metrics
- Add resource limits and requests optimization
- Set up multi-region failover capabilities
- Enhance monitoring and alerting coverage

#### Process Improvements  
- Implement canary deployment gates with SLO validation
- Add pre-production load testing requirements
- Create automated rollback triggers
- Establish change management procedures

### 6. SLO Review and Adjustment
- Analyze error budget consumption patterns
- Review SLO targets based on business requirements  
- Adjust burn rate thresholds based on operational experience
- Update alerting rules and notification channels

## Escalation & Communication

### Incident Commander
- **Primary**: DevOps Team Lead
- **Secondary**: Platform Engineering Manager  
- **Contact**: #incident-response Slack channel

### Stakeholder Notification
- **Internal**: Product team, Engineering management
- **External**: Customer support (if customer-facing impact)
- **SLA**: Notify within 15 minutes of Fast Burn alert

### Post-Incident Actions
- [ ] Root cause analysis document  
- [ ] Post-mortem meeting within 24 hours
- [ ] Action items assignment and tracking
- [ ] SLO and alerting rule review
- [ ] Runbook updates based on learnings

## Testing & Validation

### Synthetic Monitoring
```bash
# Run synthetic load test to validate recovery
bash scripts/phase5_slo_synthetic.sh

# Verify alert recovery
bash scripts/phase5_slo_verify.sh
```

### Disaster Recovery Testing
- Monthly SLO breach simulation exercises
- Quarterly full failover testing
- Annual business continuity validation

---
*Runbook Version*: 1.0  
*Last Updated*: 2025-08-28  
*Next Review*: 2025-09-28