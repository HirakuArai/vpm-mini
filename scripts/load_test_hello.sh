#!/usr/bin/env bash
set -euo pipefail

DURATION="${DURATION:-30s}"
CONCURRENCY="${CONCURRENCY:-50}"
URL="${URL:-$(kubectl get ksvc hello -o jsonpath='{.status.url}' 2>/dev/null || true)}"

if ! command -v hey >/dev/null 2>&1; then
  echo "⚠️ hey が見つかりません。Goがあれば: go install github.com/rakyll/hey@latest"
  echo "   無い場合は 'ab' (apachebench) を利用します。"; AB_FALLBACK=1
fi

START=$(date +%s)
if [ -z "${URL:-}" ]; then
  echo "✗ URL が取得できません。hello を Ready にしてから実行してください。"
  exit 1
fi
echo "Target: $URL  duration: $DURATION  concurrency: $CONCURRENCY"

TMP=$(mktemp)
if [ -z "${AB_FALLBACK:-}" ]; then
  hey -z "$DURATION" -c "$CONCURRENCY" "$URL" | tee "$TMP"
  P50=$(grep -E '^ 50%' -A0 "$TMP" | awk '{print $2}')
  ERR=$(grep -E '^Non-2xx' -A0 "$TMP" | awk '{print $3+0}' || echo 0)
else
  # ab fallback: だいたい同等のRPS把握のみ
  SECS=${DURATION%s}
  ab -k -n $((CONCURRENCY*SECS)) -c "$CONCURRENCY" "$URL/" | tee "$TMP"
  P50="(ab-no-p50)"
  ERR=$(grep 'Non-2xx responses' "$TMP" | awk '{print $3+0}' || echo 0)
fi

END=$(date +%s)
ELAPSED=$((END-START))
RPS=$(grep -E 'Requests/sec' "$TMP" | awk '{print $3+0}')
echo "RESULT p50=${P50}  errors=${ERR}  rps=${RPS}  elapsed=${ELAPSED}s"
