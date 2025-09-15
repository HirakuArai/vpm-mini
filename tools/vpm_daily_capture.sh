#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
OUT="reports/daily_status_${TS}.md"
APP_NS=${APP_NS:-hyper-swarm}
REPO=${REPO:-HirakuArai/vpm-mini}

{
  echo "# Daily Status (${TS})"
  echo "## KService"
  kubectl -n "$APP_NS" get ksvc -o wide || true
  echo -e "\n## Recent PRs"
  gh pr list --repo "$REPO" --limit 5 || true
  echo -e "\n## Merged PRs"
  gh pr list --repo "$REPO" --state merged --limit 5 || true
  echo -e "\n## Targets / Alerts (best-effort)"
  PROM_SVC=$(kubectl -n monitoring get svc -o name 2>/dev/null | grep -E 'prometheus.*' | head -n1 | cut -d/ -f2)
  if [ -n "${PROM_SVC:-}" ]; then
    (kubectl -n monitoring port-forward "svc/${PROM_SVC}" 9091:9090 >/dev/null 2>&1 & echo $! > /tmp/pf_prom.pid)
    sleep 1
    echo "### targets"
    curl -s http://localhost:9091/api/v1/targets | jq '.data.activeTargets[]?|{job:.labels.job,health:.health}' || true
    echo "### alerts"
    curl -s http://localhost:9091/api/v1/alerts | jq '.data.alerts[]?|{name:.labels.alertname,state:.state}' || true
    kill $(cat /tmp/pf_prom.pid) 2>/dev/null || true
  else
    echo "_Prometheus service not found_"
  fi
} > "$OUT"
echo "saved: $OUT"
