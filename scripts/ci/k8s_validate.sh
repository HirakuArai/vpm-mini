#!/usr/bin/env bash
set -euo pipefail

echo "[i] kubectl client:"; kubectl version --client
mkdir -p reports
OK=1

# 対象: overlays/dev と base（存在するもの）
LIST=$(ls -1 infra/k8s/overlays/dev/*.yaml 2>/dev/null || true)
LIST="$LIST "$(ls -1 infra/k8s/base/**/*.yaml 2>/dev/null || true)

if [ -z "${LIST// }" ]; then
  echo "[!] no manifests found under infra/k8s"; exit 0
fi

for f in ${LIST}; do
  echo "::group::validate $f"
  if ! kubectl apply --dry-run=client -f "$f" >/dev/null; then
    echo "::error file=$f::validation failed"
    OK=0
  else
    echo "ok: $f"
  fi
  echo "::endgroup::"
done

TS=$(date +%Y%m%d_%H%M%S)
OUT="reports/p2_3_ci_validate_${TS}.json"
if [ "$OK" -eq 1 ]; then
  echo '{"k8s_validate":"ok","ts":"'"$TS"'"}' > "$OUT"
  echo "[✓] validation passed -> $OUT"
  exit 0
else
  echo '{"k8s_validate":"fail","ts":"'"$TS"'"}' > "$OUT"
  echo "[x] validation failed -> $OUT"
  exit 1
fi
