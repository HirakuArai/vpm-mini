#!/usr/bin/env bash
set -euo pipefail
echo "[healthcheck] start"
if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; S1 stage -> skip"
  exit 0
fi
docker compose up -d --wait
for i in {1..10}; do
  if docker compose ps --format json | jq -e 'all(.[]?; .Health == "healthy")' >/dev/null; then
    echo "[healthcheck] OK"; exit 0
  fi
  echo "[healthcheck] waiting healthy ($i/10)"; sleep 3
done
echo "[healthcheck] some services are not healthy" >&2
exit 1