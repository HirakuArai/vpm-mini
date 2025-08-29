#!/usr/bin/env bash
set -euo pipefail
NAME="${NAME:-vpm-edge-haproxy}"
CFG="${CFG:-edge/haproxy/haproxy.cfg.tmpl}"

command -v docker >/dev/null || { echo "docker not found"; exit 1; }
[ -f "$CFG" ] || { echo "missing $CFG"; exit 1; }

echo "[edge] start HAProxy container → http://localhost:30080/hello"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" \
  -p 30080:30080 -p 30090:30090 \
  -v "$(pwd)/$CFG:/usr/local/etc/haproxy/haproxy.cfg:ro" \
  --health-cmd='wget -qO- http://127.0.0.1:30090/stats || exit 1' \
  --health-interval=5s --health-retries=10 \
  haproxy:2.9-alpine >/dev/null

# 簡易疎通
for i in {1..10}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://localhost:30080/hello || true)
  if [ "$code" = "200" ]; then echo "[edge] OK: 200"; exit 0; fi
  sleep 1
done
echo "[edge] WARN: /hello 200未達（続行は可）"