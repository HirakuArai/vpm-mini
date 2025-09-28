#!/usr/bin/env bash
set -euo pipefail
KSVC_YAML="${1:-/tmp/ksvc_ready.yaml}"
TS="$(date -u +%Y%m%d_%H%M%S)"
OUT="reports/evidence_kservice_ready_${TS}.md"
mkdir -p reports

READY="Unknown"
if [[ -f "$KSVC_YAML" ]]; then
  if command -v yq >/dev/null 2>&1; then
    READY="$(yq -r '.status.conditions[] | select(.type=="Ready") | .status // "Unknown"' "$KSVC_YAML" 2>/dev/null | head -n1 || echo "Unknown")"
  fi
  if [[ "$READY" == "Unknown" ]]; then
    # フォールバック：Ready セクション内の status を次の type ブロックまで探索
    READY="$(awk '
      BEGIN{ready="Unknown"; in=0}
      /^[[:space:]]*- +type:[[:space:]]*Ready/ {in=1; next}
      in==1 && /^[[:space:]]*- +type:/ {in=0}
      in==1 && /status:[[:space:]]*"?True"?/ {ready="True"; in=0}
      END{print ready}
    ' "$KSVC_YAML" 2>/dev/null || echo "Unknown")"
  fi
fi

RESULT="FAIL"; [[ "$READY" == "True" ]] && RESULT="PASS"

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