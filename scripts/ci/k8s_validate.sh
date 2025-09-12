#!/usr/bin/env bash
set -euo pipefail

echo "[i] kubectl client:"; kubectl version --client
mkdir -p reports
OK=1

# 対象: overlays/dev と base（存在するもの）
LIST=$(ls -1 infra/k8s/overlays/dev/*.yaml 2>/dev/null || true)
LIST="$LIST "$(find infra/k8s/overlays/dev -name "*.yaml" 2>/dev/null || true)
LIST="$LIST "$(find infra/k8s/base -name "*.yaml" 2>/dev/null || true)

if [ -z "${LIST// }" ]; then
  echo "[!] no manifests found under infra/k8s"; exit 0
fi

for f in ${LIST}; do
  echo "::group::validate $f"
  # Basic YAML syntax check + required K8s fields
  if ! python3 -c "
import yaml, sys
try:
    with open('$f') as file:
        docs = list(yaml.safe_load_all(file))
        for doc in docs:
            if doc is None: continue
            if not isinstance(doc, dict):
                raise ValueError('Document is not a dict')
            if 'apiVersion' not in doc or 'kind' not in doc:
                raise ValueError('Missing apiVersion or kind')
        print('✓ Valid YAML with K8s structure')
except Exception as e:
    print(f'✗ {e}', file=sys.stderr)
    sys.exit(1)
  " 2>/dev/null; then
    echo "::error file=$f::validation failed"
    OK=0
  else
    echo "ok: $f"
  fi
  echo "::endgroup::"
done

# Kustomize validation for hello-ai
if [ -d "infra/k8s/overlays/dev/hello" ]; then
  echo "::group::kustomize validate infra/k8s/overlays/dev/hello"
  if command -v kustomize >/dev/null 2>&1; then
    if kustomize build infra/k8s/overlays/dev/hello > /dev/null; then
      echo "✓ kustomize build succeeded for hello"
    else
      echo "::error::kustomize build failed for hello"
      OK=0
    fi
  else
    echo "::warning::kustomize not available, skipping kustomize validation"
  fi
  echo "::endgroup::"
fi

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
