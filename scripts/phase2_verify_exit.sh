#!/usr/bin/env bash
set -euo pipefail

stamp(){ date +%Y-%m-%dT%H:%M:%S%z; }
field(){ v="$1"; [ -z "$v" ] && echo "n/a" || echo "$v"; }

TS=$(stamp)
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo n/a)
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo n/a)

HELLO_READY=" "
AUTOSCALE_OK=" "
MON_OK=" "
PERF_OK=" "

HELLO_URL=""
MAXR=""
P50=""
RPS=""
ERRS=""
NOTES="no live cluster; relying on prior PR artifacts"

if kubectl cluster-info >/dev/null 2>&1; then
  # Hello Ready
  if kubectl get ksvc hello >/dev/null 2>&1; then
    if kubectl get ksvc hello -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q True; then
      HELLO_READY="x"
      HELLO_URL="$(kubectl get ksvc hello -o jsonpath='{.status.url}')"
    fi
  fi

  # Autoscale: 観測ベース（現在のPod数>1ならOK。なければn/a）
  MAXR=$(kubectl get pods -l serving.knative.dev/service=hello --no-headers 2>/dev/null | wc -l | awk '{print $1}')
  [ -n "$MAXR" ] && [ "$MAXR" -ge 2 ] && AUTOSCALE_OK="x"

  # Monitoring stack
  if kubectl -n monitoring get deploy prometheus grafana >/dev/null 2>&1; then
    POK=$(kubectl -n monitoring get deploy prometheus -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null)
    GOK=$(kubectl -n monitoring get deploy grafana -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null)
    if echo "$POK$GOK" | grep -q True; then MON_OK="x"; fi
  fi

  # Perf（存在すれば hey/ab 直近結果から拾う）— 任意
  if [ -f /tmp/load_max50.txt ]; then
    P50=$(grep -E 'p50=| 50%' /tmp/load_max50.txt | head -n1 | sed -E 's/.*p50=([^ ]+).*/\1/;t; s/.* 50%[[:space:]]+([^ ]+).*/\1/')
    RPS=$(grep -E 'Requests/sec' /tmp/load_max50.txt | awk '{print $3+0}')
    ERRS=$(grep -E 'Non-2xx|errors=' /tmp/load_max50.txt | head -n1 | sed -E 's/.*errors=([0-9]+).*/\1/;t; s/.*Non-2xx responses: ([0-9]+).*/\1/'; true)
    [ -z "$ERRS" ] && ERRS=0
    # ラフ判定
    if [ -n "$P50" ]; then
      # p50が 1s 未満か大雑把に判定（ms or s を含むケースの簡易判定）
      if echo "$P50" | grep -Eq 'ms'; then PERF_OK="x"
      elif echo "$P50" | grep -Eq '(^0\.[0-9]+s$)|(^[0-1](\.[0-9]+)?s$)'; then PERF_OK="x"
      fi
    fi
    NOTES="live cluster verified"
  fi
fi

# テンプレに流し込み
OUT="reports/phase2_exit_status_$(date +%Y%m%d-%H%M%S).md"
sed "s/{{ts}}/$TS/; s/{{commit}}/$COMMIT/; s/{{branch}}/$BRANCH/; \
s/{{hello_ready}}/$HELLO_READY/; s/{{autoscale_ok}}/$AUTOSCALE_OK/; s/{{monitoring_ok}}/$MON_OK/; s/{{perf_ok}}/$PERF_OK/; \
s#{{hello_url}}#$(field "$HELLO_URL")#; s/{{max_replicas}}/$(field "$MAXR")/; \
s/{{p50}}/$(field "$P50")/; s/{{rps}}/$(field "$RPS")/; s/{{errors}}/$(field "$ERRS")/; \
s#{{notes}}#$(echo "$NOTES" | sed 's/[&/]/\\&/g')#" \
reports/templates/phase2_exit_checklist.md.tmpl > "$OUT"

echo "Wrote $OUT"
