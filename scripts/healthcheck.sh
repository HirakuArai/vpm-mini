#!/usr/bin/env bash
set -euo pipefail
echo "[healthcheck] start"

# S1互換：composeが無ければスキップ成功
if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; skip for S1"
  exit 0
fi

# compose 構文検証（ここで落ちるなら早期に原因がわかる）
if ! docker compose config -q; then
  echo "[healthcheck] ERROR: docker compose config failed" >&2
  exit 1
fi

# 起動→ヘルス監視（最大30秒）
docker compose up -d --wait || true
need_jq=true; command -v jq >/dev/null 2>&1 && need_jq=false
if $need_jq; then echo "[healthcheck] WARN: jq not found, installing may be required in CI"; fi

tries=0
until docker compose ps --format json | jq -s -e "map(select(.Service != \"redis\")) | all(.Health == \"healthy\")" >/dev/null 2>&1; do
  tries=$((tries+1))
  if [[ $tries -ge 10 ]]; then
    echo "[healthcheck] FAIL: services not healthy after ${tries} tries" >&2
    docker compose ps || true
    docker compose logs --no-color --tail=200 || true
    exit 1
  fi
  echo "[healthcheck] waiting for healthy (${tries}/10)"
  sleep 3
done

echo "[healthcheck] OK"
docker compose down -v || true