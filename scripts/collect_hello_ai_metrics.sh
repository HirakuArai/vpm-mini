#!/usr/bin/env bash
set -euo pipefail
NS=${NS:-hyper-swarm}
APP=${APP:-hello-ai}
N=${1:-12}

URL_HOST=$(kubectl -n "$NS" get ksvc "$APP" -o jsonpath='{.status.url}' | sed -E 's#^https?://##')
# port-forward
kubectl -n kourier-system port-forward svc/kourier 8080:80 >/tmp/pf_hello_ai.log 2>&1 &
PF=$!
cleanup(){ kill $PF >/dev/null 2>&1 || true; }
trap cleanup EXIT
sleep 2

WORK="/tmp/hello_ai_metrics.$$"
mkdir -p "$WORK"
RAW="$WORK/raw.tsv"   # ts  status  dur  fb  trace
: > "$RAW"

for i in $(seq 1 "$N"); do
  RESP=$(curl -isS -H "Host: ${URL_HOST}" "http://127.0.0.1:8080/hello-ai?msg=ping&i=$i")
  ST=$(printf "%s" "$RESP" | head -n1 | awk '{print $2}')
  DUR=$(printf "%s" "$RESP" | awk -F': ' 'BEGIN{IGNORECASE=1}/^X-Dur-Ms:/{gsub(/\r/,"",$2);print $2}' | tail -n1)
  FB=$(printf "%s" "$RESP" | awk -F': ' 'BEGIN{IGNORECASE=1}/^X-Fallback:/{gsub(/\r/,"",$2);print tolower($2)}' | tail -n1)
  TR=$(printf "%s" "$RESP" | awk -F': ' 'BEGIN{IGNORECASE=1}/^X-Trace-Id:/{gsub(/\r/,"",$2);print $2}' | tail -n1)
  TS_NOW=$(date '+%Y-%m-%dT%H:%M:%S')
  printf "%s\t%s\t%s\t%s\t%s\n" "$TS_NOW" "${ST:-NA}" "${DUR:-NA}" "${FB:-na}" "${TR:-na}" >> "$RAW"
done

# 集計
TOTAL=$(wc -l < "$RAW" | tr -d ' ')
HTTP200=$(awk '$2=="200"' "$RAW" | wc -l | tr -d ' ')
FB_TRUE=$(awk '$4=="true"' "$RAW" | wc -l | tr -d ' ')
FB_FALSE=$(awk '$4=="false"' "$RAW" | wc -l | tr -d ' ')
# 数値だけ拾って平均/中央値/95p
DURS=$(awk '$3 ~ /^[0-9]+$/{print $3}' "$RAW")
if [ -n "$DURS" ]; then
  AVG=$(awk '{s+=$1}END{if(NR>0)printf("%.0f",s/NR);else print "NA"}' <<< "$DURS")
  SORTED=$(sort -n <<< "$DURS")
  CNT=$(wc -l <<< "$SORTED" | tr -d ' ')
  P50_IDX=$(( (CNT+1)/2 ))
  P95_IDX=$(( (CNT*95+99)/100 ))
  P50=$(awk 'NR==i{print;exit}' i="$P50_IDX" <<< "$SORTED")
  P95=$(awk 'NR==i{print;exit}' i="$P95_IDX" <<< "$SORTED")
else
  AVG="NA"; P50="NA"; P95="NA"
fi

TS=$(date +%Y%m%d_%H%M%S)
OUT_JSON="reports/p2_4_obs_${TS}.json"
OUT_MD="reports/p2_4_obs_${TS}.md"

# JSON
jq -n --arg ns "$NS" --arg app "$APP" \
  --argjson total "$TOTAL" --argjson http200 "$HTTP200" \
  --argjson fb_true "$FB_TRUE" --argjson fb_false "$FB_FALSE" \
  --arg p50 "$P50" --arg p95 "$P95" --arg avg "$AVG" \
  --arg url_host "$URL_HOST" \
  '{ns:$ns, app:$app, total:$total, http200:$http200, fallback_true:$fb_true, fallback_false:$fb_false,
    p50_ms:($p50|tonumber?), p95_ms:($p95|tonumber?), avg_ms:($avg|tonumber?),
    url_host:$url_host, generated_at:(now|todate)}' > "$OUT_JSON"

# Markdown（生データの先頭数行だけ貼る）
{
  echo "# P2-4 Observability Evidence (${TS})"
  echo
  echo "- ksvc host: \`$URL_HOST\`"
  echo "- requests: $TOTAL, 200: $HTTP200, fallback_true: $FB_TRUE, fallback_false: $FB_FALSE"
  echo "- p50: ${P50} ms / p95: ${P95} ms / avg: ${AVG} ms"
  echo
  echo "## sample raw (head)"
  echo '```tsv'
  head -n 8 "$RAW"
  echo '```'
} > "$OUT_MD"

echo "$OUT_JSON"   # 呼び出し側が受け取りやすいようにパスを出力
