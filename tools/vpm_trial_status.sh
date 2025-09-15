#!/usr/bin/env bash
set -euo pipefail
APP_NS=${APP_NS:-hyper-swarm}
REPO=${REPO:-HirakuArai/vpm-mini}

echo "== KService (ns=$APP_NS) =="
kubectl -n "$APP_NS" get ksvc -o wide || true

echo "== Recent PRs =="
gh pr list --repo "$REPO" --limit 5 || true
echo "== Merged PRs =="
gh pr list --repo "$REPO" --state merged --limit 5 || true

PROM_SVC=$(kubectl -n monitoring get svc -o name 2>/dev/null | grep -E 'prometheus.*' | head -n1 | cut -d/ -f2)
if [ -n "${PROM_SVC:-}" ]; then
  (kubectl -n monitoring port-forward "svc/${PROM_SVC}" 9091:9090 >/dev/null 2>&1 & echo $! > /tmp/pf_prom.pid)
  sleep 1
  echo "== Targets (hello-ai & peers) =="
  curl -s http://localhost:9091/api/v1/targets | jq '.data.activeTargets[]|{job:.labels.job,health:.health}|select(.job|test("hello-ai|watcher|curator|planner|synthesizer|archivist"))' || true
  echo "== Alerts (HelloAI* / SLO*) =="
  curl -s http://localhost:9091/api/v1/alerts | jq '.data.alerts[]?|select(.labels.alertname|test("HelloAI|SLO"))|{name:.labels.alertname,state:.state,activeAt:.activeAt}' || true
  kill $(cat /tmp/pf_prom.pid) 2>/dev/null || true
else
  echo "Prometheus service not found in monitoring ns."
fi
