#!/usr/bin/env bash
set -euo pipefail
echo "[healthcheck] start"
if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; skip for S1"
  exit 0
fi
docker compose up -d --wait
sleep 3
docker compose ps
# 全ての行に 'healthy' を含むか（ヘッダ除外）
if ! docker compose ps --format json | jq -e 'all(.[]?; .Health == "healthy")' >/dev/null 2>&1; then
  echo "[healthcheck] some services are not healthy" >&2
  exit 1
fi
echo "[healthcheck] OK"