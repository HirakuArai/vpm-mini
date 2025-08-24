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
until docker compose ps --format json | jq -s -e "all(.Health == \"healthy\")" >/dev/null 2>&1; do
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

# S8: Prometheus targets verification (3 retries)
if docker compose ps --format json | jq -s -e 'any(.Service == "prometheus")' >/dev/null 2>&1; then
  PROM="http://localhost:9090/api/v1/targets"
  for i in 1 2 3; do
    echo "[prometheus] checking targets (${i}/3)"
    if curl -fsS "$PROM" 2>/dev/null | grep -q '"health":"up"'; then
      echo "[prometheus] targets up"
      break
    fi
    if [[ $i -eq 3 ]]; then
      echo "[healthcheck] FAIL: prometheus targets not healthy after 3 tries" >&2
      curl -fsS "$PROM" || echo "[prometheus] targets endpoint failed" >&2
      exit 1
    fi
    sleep 3
  done
fi

echo "[healthcheck] OK"
docker compose down -v || true
