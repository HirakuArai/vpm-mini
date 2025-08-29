#!/usr/bin/env bash
set -euo pipefail
OUT=reports/phase5_failover_result.json
EDGE_URL=${EDGE_URL:-http://localhost:30080/hello}
A_CTX=${A_CTX:-kind-cluster-a}
A_NS=${A_NS:-istio-system}
A_DEP=${A_DEP:-istio-ingressgateway}

succ_p50 () { # $1=url $2=shots
  local url=$1 n=${2:-200} ok=0; local t0 t1 code; local arr=()
  for i in $(seq 1 $n); do
    t0=$(date +%s%3N)
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" || true)
    t1=$(date +%s%3N); arr+=($((t1-t0)))
    [ "$code" = "200" ] && ok=$((ok+1))
    sleep 0.02
  done
  local p50
  p50=$(python3 - <<PY ${arr[@]}
import sys,statistics;print(int(statistics.median(map(int,sys.argv[1:]))))
PY
)
  echo "$ok $n $p50"
}

mkdir -p reports

echo "[precheck] probing edge..."
read ok n p50 < <(succ_p50 "$EDGE_URL" 50)
echo "[precheck] ok=$ok/$n p50=${p50}ms"

echo "[fault] scale down $A_NS/$A_DEP in $A_CTX"
kubectl --context "$A_CTX" -n "$A_NS" scale deploy "$A_DEP" --replicas=0

echo "[wait] detecting switchover to backup..."
ts=$(date +%s); good=0
while :; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$EDGE_URL" || true)
  if [ "$code" = "200" ]; then good=$((good+1)); else good=0; fi
  [ $good -ge 10 ] && break
  sleep 1
done
rto=$(( $(date +%s) - ts ))

echo "[measure] quality after switch..."
read ok n p50 < <(succ_p50 "$EDGE_URL" 300)
succ=$(python3 - <<PY
ok=$ok; n=$n
print(round(ok/n,3))
PY
)

# best-effort 回復（失敗しても続行）
kubectl --context "$A_CTX" -n "$A_NS" scale deploy "$A_DEP" --replicas=1 || true

jq -n --argjson rto $rto --argjson succ $succ --argjson p50 $p50 \
  '{rto_sec:rto, success_rate:succ, p50_ms:p50, switched_to:"cluster-b",
    all_ok:( (rto<=60) and (succ>=0.95) and (p50<1000) ) }' \
  | tee "$OUT"

[ "$(jq -r '.all_ok' "$OUT")" = "true" ] && echo "[OK] failover drill passed" || (echo "[NG] failover failed"; exit 1)

DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ"); COMMIT=$(git rev-parse --short HEAD)
sed -e "s|{{DATE}}|$DATE|g" \
    -e "s|{{COMMIT}}|$COMMIT|g" \
    -e "s|{{VERIFY_JSON}}|$OUT|g" \
    reports/templates/phase5_failover_report.md.tmpl > reports/snap_phase5-5-failover.md