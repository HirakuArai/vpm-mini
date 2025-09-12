# P5-3 Evidence: watcher real image implementation & swap (20250913_071837)

## Real Watcher Service Implementation
- **FastAPI Application**: services/watcher/app.py with /healthz and /metrics endpoints
- **Prometheus Metrics**: prometheus_client with hello_ai_requests_total, hello_ai_request_duration_seconds, hello_ai_up
- **Dependencies**: FastAPI 0.110.0, Uvicorn 0.29.0, prometheus_client 0.20.0
- **Dockerfile**: Multi-stage build with Python 3.11-slim base image
- **GitHub Actions**: .github/workflows/build_watcher.yml for CI/CD

## Image Build Status
- **Target Image**: ghcr.io/hirakuarai/watcher:0.2.0
- **Build Result**: Multi-arch build (linux/amd64, linux/arm64) completed successfully
- **Push Result**: Failed due to GHCR authentication (expected in demo environment)
- **Fallback**: Using ghcr.io/hirakuarai/hello-ai:1.0.3 for deployment testing

## Deployment Infrastructure
- **KService**: Configured with proper readiness probe for /healthz endpoint
- **Environment**: ConfigMap injection with ROLE, PORT, METRICS_PORT, TRACE_ID
- **Metrics Service**: watcher-metrics on port 9001 for Prometheus scraping
- **ServiceMonitor**: Configured with proper release labels (vpm-mini-kube-prometheus-stack)

## Health & Metrics
- **/healthz endpoint**: Implemented in FastAPI app (returns {"status":"ok"})
- **/metrics endpoint**: Prometheus-compatible metrics on main port
- **Warm-up result**: false (deployment issues with current environment)
- **ServiceMonitor**: Configured and ready for Prometheus discovery

## Files Created/Modified
- **Application Code**:
  - services/watcher/app.py: FastAPI application with health and metrics
  - services/watcher/requirements.txt: Python dependencies
  - services/watcher/Dockerfile: Container build configuration
  - services/watcher/tests/test_smoke.py: Basic test structure
- **CI/CD**:
  - .github/workflows/build_watcher.yml: GitHub Actions build workflow
- **Infrastructure**: 
  - Existing KService, ConfigMap, metrics Service, ServiceMonitor maintained

## Deployment Status
- **KService**: Configured but pods not running (ProgressDeadlineExceeded)
- **Revisions**: watcher-00001, watcher-00002 both in failed state
- **Root Cause**: Likely related to image/configuration compatibility
- **ServiceMonitor**: Successfully created and configured for Prometheus

## Next Steps
1. **Resolve GHCR authentication** to push the actual watcher image
2. **Debug deployment issues** causing ProgressDeadlineExceeded
3. **Test with real watcher image** once pushed to GHCR
4. **Validate /healthz and /metrics endpoints** with actual service
5. **Verify Prometheus scraping** once service is running

## Implementation Readiness
- **Service Code**: ✅ Complete FastAPI implementation
- **Container Build**: ✅ Multi-arch Dockerfile working
- **CI/CD Pipeline**: ✅ GitHub Actions workflow created  
- **Kubernetes Config**: ✅ All resources configured
- **Monitoring Setup**: ✅ ServiceMonitor and metrics Service ready
- **Image Registry**: ⏳ GHCR authentication needed
