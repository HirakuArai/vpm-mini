#!/usr/bin/env bash
# Usage: knative_canary.sh <kubeconfig_path> <namespace> <ksvc_name> <canary_percent>
set -euo pipefail

KCONF="$1"; NS="$2"; KNAME="$3"; PCT="$4"
export KUBECONFIG="$KCONF"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

# 0) 参照情報
URL=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.url}' 2>/dev/null || true)
STABLE=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.latestReadyRevisionName}' 2>/dev/null || true)
log "ksvc=$KNAME url=${URL:-N/A} stable=${STABLE:-N/A}"

if [ -z "${STABLE}" ]; then
  log "No stable revision yet; applying manifest as baseline (100%)."
  kubectl -n "$NS" apply -f infra/k8s/overlays/dev/${KNAME}-ksvc.yaml
  # 待機
  for i in $(seq 1 60); do
    READY=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' || true)
    [ "$READY" = "True" ] && break
    sleep 2
  done
  STABLE=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.latestReadyRevisionName}')
fi

# 1) Canary 配置：stable(100-PCT) / latestRevision(PCT)
log "Stage: Canary ${PCT}%"
cat <<PATCH | kubectl -n "$NS" patch ksvc "$KNAME" --type=merge -p "$(cat)"
{
  "spec": {
    "traffic": [
      { "revisionName": "${STABLE}", "percent": $((100-PCT)) },
      { "latestRevision": true, "percent": ${PCT} }
    ]
  }
}
PATCH

# 新規リビジョンの Ready 待機
for i in $(seq 1 60); do
  READY=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' || true)
  [ "$READY" = "True" ] && break
  sleep 2
done

# 2) Guard：URL 200 確認（3回まで）
URL=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.url}')
log "Guard check: ${URL}"
ok=0
for i in 1 2 3; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$code" = "200" ]; then ok=1; break; fi
  sleep 2
done
if [ "$ok" != "1" ]; then
  log "Guard failed on canary. Rolling back to ${STABLE} (100%)."
  cat <<ROLL | kubectl -n "$NS" patch ksvc "$KNAME" --type=merge -p "$(cat)"
{ "spec": { "traffic": [ { "revisionName": "${STABLE}", "percent": 100 } ] } }
ROLL
  exit 1
fi

# 3) Promote：100% 最新
log "Stage: Promote 100%"
NEWREV=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.latestCreatedRevisionName}')
cat <<PROMO | kubectl -n "$NS" patch ksvc "$KNAME" --type=merge -p "$(cat)"
{ "spec": { "traffic": [ { "revisionName": "${NEWREV}", "percent": 100 } ] } }
PROMO

# Ready 待機
for i in $(seq 1 60); do
  READY=$(kubectl -n "$NS" get ksvc "$KNAME" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' || true)
  [ "$READY" = "True" ] && break
  sleep 2
done

# 4) Post-Guard：200 確認（3回まで）
ok=0
for i in 1 2 3; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$code" = "200" ]; then ok=1; break; fi
  sleep 2
done
if [ "$ok" != "1" ]; then
  log "Post-Guard failed after promote. Rolling back to ${STABLE} (100%)."
  cat <<ROLL2 | kubectl -n "$NS" patch ksvc "$KNAME" --type=merge -p "$(cat)"
{ "spec": { "traffic": [ { "revisionName": "${STABLE}", "percent": 100 } ] } }
ROLL2
  exit 1
fi

log "Done: Promote success."