#!/usr/bin/env bash
set -euo pipefail

# 入力: KSVCの状態YAML (例: /tmp/ksvc_ready.yaml)
KSVC_YAML="${1:-/tmp/ksvc_ready.yaml}"
TS="$(date -u +%Y%m%d_%H%M%S)"
OUT="reports/evidence_kservice_ready_${TS}.md"
mkdir -p reports

if [[ ! -f "$KSVC_YAML" ]]; then
  echo "::warning::KSVC YAML not found: $KSVC_YAML (writing placeholder evidence)"
  READY="Unknown"
else
  # "type: Ready" セクション直後の "status: True" を検出
  if awk '
    $0 ~ /type:[[:space:]]*Ready/ {flag=1; next}
    flag==1 { if ($0 ~ /status:[[:space:]]*"?True"?/) {print "True"; exit}; flag=0 }
  ' "$KSVC_YAML" | grep -q True; then
    READY="True"
  else
    READY="False"
  fi
fi

RESULT="FAIL"
[[ "$READY" == "True" ]] && RESULT="PASS"

cat > "$OUT" <<EOF
# Knative Service READY Evidence

- generatedAt: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- source: $KSVC_YAML

## Ready Status

- READY: "$READY"

## Full Conditions

\`\`\`yaml
$(cat "$KSVC_YAML" 2>/dev/null || echo "(no ksvc yaml)")
\`\`\`

## Verification
- READY status extracted: "$READY"
- Expected: True
- Result: $RESULT
EOF

echo "Wrote $OUT"