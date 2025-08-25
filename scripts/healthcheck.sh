#!/usr/bin/env bash
set -euo pipefail
echo "[healthcheck] start"

if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; skip"
  exit 0
fi

docker compose version
docker compose config -q

docker compose up -d --wait || true

# roles（redis/prometheus/grafana除く）の healthy 待ち
for i in {1..12}; do
  ok=$(docker compose ps --format json | jq -s -r '
    map(select(.Service!="redis" and .Service!="prometheus" and .Service!="grafana"))
    | all(.Health=="healthy")')
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

# Targets が 'unknown' → 'up' に遷移するまで十分に待つ（スクレイプ完了待ち）
for i in {1..12}; do
  curl -fsS 'http://localhost:9090/api/v1/targets' -o reports/s8_targets.json || true
  all_up=$(jq -r '([.data.activeTargets[]?.health]=="up") as $x | if $x then "true" else ( [.data.activeTargets[]?.health] | all(.=="up") ) end' reports/s8_targets.json || echo false)
  # 上の式は "全て up" を厳密に見る。unknown が混ざる間は false。
  if [[ "$all_up" == "true" ]]; then
    echo "[healthcheck] targets up at try $i"
    break
  fi
  if [[ $i -eq 12 ]]; then
    echo "[healthcheck] targets not up"
    jq '.data.activeTargets[] | {url:.scrapeUrl, health:.health, lastError:.lastError}' reports/s8_targets.json || true
    exit 1
  fi
  sleep 5
done

# up==1 のクエリでも確認（冗長だが診断に便利）
curl -fsS 'http://localhost:9090/api/v1/query?query=up' -o reports/s8_query_up.json || true
jq -e 'all(.data.result[]?; .value[1]=="1")' reports/s8_query_up.json >/dev/null || {
  echo "[healthcheck] query up != 1 somewhere"; jq '.data.result' reports/s8_query_up.json || true; exit 1; }

docker compose ps > reports/s8_compose_ps.txt
echo 0 > reports/s8_exit.code
docker compose down -v || true
echo "[healthcheck] OK"