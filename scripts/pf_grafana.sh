#!/usr/bin/env bash
set -euo pipefail

NS=${NS:-monitoring}
SVC=$(kubectl -n "$NS" get svc -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}')
if [ -z "${SVC:-}" ]; then
  echo "Grafana Service not found in ns=$NS" >&2
  exit 1
fi
>&2 echo "→ Port-forward $SVC (ns=$NS) to http://localhost:3000 (Ctrl-C to stop)"
kubectl -n "$NS" port-forward "svc/$SVC" 3000:80
