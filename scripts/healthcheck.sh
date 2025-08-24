#!/usr/bin/env bash
set -euo pipefail
echo "[healthcheck] start"

# S1 互換
if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; skip"
  exit 0
fi

# 構文検証
docker compose version
docker compose config -q

# 起動
docker compose up -d --wait || true

# roles 健康待ち（redis/prometheusは除外）
for i in {1..12}; do
  ok=$(docker compose ps --format json | jq -s -r '
    map(select(.Service != "redis" and .Service != "prometheus"))
    | all(.Health == "healthy")')
  if [[ "$ok" == "true" ]]; then
    echo "[healthcheck] roles healthy at try $i"
    break
  fi
  [[ $i -eq 12 ]] && { echo "[healthcheck] roles not healthy"; docker compose ps; docker compose logs --no-color --tail=200; exit 1; }
  sleep 5
done

# Prometheus readiness
for i in {1..12}; do
  if curl -fsS http://localhost:9090/-/ready >/dev/null; then
    echo "[healthcheck] prometheus ready at try $i"
    break
  fi
  [[ $i -eq 12 ]] && { echo "[healthcheck] prometheus not ready"; docker compose logs --no-color prometheus | tail -n 200; exit 1; }
  sleep 5
done

# Targets UP 確認
curl -fsS 'http://localhost:9090/api/v1/targets' | tee reports/s8_targets.json >/dev/null
up=$(jq -r '[.data.activeTargets[].health] | all(.=="up")' reports/s8_targets.json)
[[ "$up" == "true" ]] || { echo "[healthcheck] targets not up"; jq '.data.activeTargets[]|{url:.scrapeUrl,health:.health,lastError:.lastError}' reports/s8_targets.json; exit 1; }

# up クエリ確認
curl -fsS 'http://localhost:9090/api/v1/query?query=up' | tee reports/s8_query_up.json >/dev/null
jq -e 'all(.data.result[]?; .value[1]=="1")' reports/s8_query_up.json >/dev/null

# 証跡・終了
docker compose ps > reports/s8_compose_ps.txt
echo 0 > reports/s8_exit.code
docker compose down -v || true
echo "[healthcheck] OK"