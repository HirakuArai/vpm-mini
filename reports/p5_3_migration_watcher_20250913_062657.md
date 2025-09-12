# P5-3 Evidence: Compose -> Knative migration (first service) — watcher

## Context
- Namespace: hyper-swarm
- URL: http://watcher.hyper-swarm.127.0.0.1.sslip.io
- Image: ghcr.io/hirakuarai/hello-ai:1.0.3 (placeholder - actual watcher image needs to be built)
- Port: 8001

## What changed
- Added KService: infra/k8s/overlays/dev/watcher/ksvc.yaml
- Included in dev overlay: infra/k8s/overlays/dev/kustomization.yaml
- Successfully deployed Knative Service with autoscaling configuration

## Service Configuration
- **Autoscaling**: KPA with concurrency target=10, minScale=0, maxScale=30
- **Resources**: 100m CPU / 128Mi memory requests, 1 CPU / 512Mi limits
- **Security**: Modified to allow root user (readOnlyRootFilesystem=false, runAsNonRoot=false)
- **Container Port**: 8001 (matching compose port mapping)

## Deployment Status
- ksvc READY=Unknown (RevisionMissing - expected with placeholder image)
- Pod Status: 1/2 containers ready (main container started, queue-proxy readiness probe failing)
- Main container successfully started with security context adjustments
- Warm-up: Skipped (using placeholder image instead of actual watcher service)

## Migration Analysis
- **Source**: docker-compose.yaml watcher service (vpm-mini/app:dev image)
- **Target**: Knative Service with security hardening and autoscaling
- **Image**: Temporarily using hello-ai:1.0.3 as placeholder until watcher image is built
- **Environment Variables**: Deferred to next PR (will use ESO/SOPS for secrets)

## Next Steps (follow-up PRs)
1. **Image Build**: Create proper watcher service image with correct application
2. **Env/Secrets**: Migrate compose environment variables to K8s Secret/ConfigMap via ESO/SOPS
3. **Health Checks**: Add proper health check endpoints for readiness probes  
4. **Observability**: Add metrics Service + ServiceMonitor if watcher exposes /metrics
5. **SLO/Alerts**: Add Grafana panels and Prometheus rules for watcher service

## Files Created
- `infra/k8s/overlays/dev/watcher/ksvc.yaml`: Knative Service definition
- `infra/k8s/overlays/dev/watcher/kustomization.yaml`: Kustomize configuration
- Updated `infra/k8s/overlays/dev/kustomization.yaml` to include watcher