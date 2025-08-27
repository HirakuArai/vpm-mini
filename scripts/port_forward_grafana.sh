#!/usr/bin/env bash
set -euo pipefail
NAMESPACE="${NAMESPACE:-monitoring}"
PORT="${PORT:-3000}"
echo "Port-forward Grafana on http://localhost:${PORT}"
kubectl -n "$NAMESPACE" port-forward svc/grafana "${PORT}:3000"
