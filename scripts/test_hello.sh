#!/usr/bin/env bash
set -euo pipefail

NS=${NS:-kourier-system}
FORCE_PF=${FORCE_PF:-0}
URL="$(kubectl get ksvc hello -o jsonpath='{.status.url}')"
HOST="${URL#http://}"
HOST="${HOST#https://}"

NP_HTTP="$(kubectl -n "${NS}" get svc kourier -o jsonpath='{range .spec.ports[*]}{.name}:{.port}:{.nodePort}->{.targetPort}{"\n"}{end}' \
  | awk -F ':' '/^http/ {node=$3; sub(/->.*/, "", node); if (node ~ /^[0-9]+$/) {print node; exit}}')"

if [[ "${FORCE_PF}" != "1" && -n "${NP_HTTP}" ]]; then
  echo "== via NodePort :${NP_HTTP}"
  set +e
  LINE="$(curl -i -sS -H "Host: ${HOST}" "http://127.0.0.1:${NP_HTTP}/" 2>/dev/null | head -n 1)"
  RC=$?
  set -e
  printf "%s\n" "${LINE}"
  if [[ ${RC} -eq 0 ]]; then
    exit 0
  fi
  echo "NodePort access failed, falling back to port-forward"
fi

echo "== via port-forward 8080:8080"
kubectl -n "${NS}" port-forward deploy/3scale-kourier-gateway 8080:8080 >/tmp/kourier_pf.log 2>&1 &
PF=$!
trap 'kill ${PF} 2>/dev/null || true' EXIT
sleep 2
curl -i -sS -H "Host: ${HOST}" "http://127.0.0.1:8080/" | head -n 1
