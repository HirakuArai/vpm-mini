#!/usr/bin/env bash
set -euo pipefail

# Phase 5 SLO Verification
# Check if fast/slow burn alerts were triggered and recovery is OK

PROM_URL=${PROM_URL:-http://localhost:30090}
OUTPUT_FILE=${OUTPUT_FILE:-reports/phase5_slo_verify.json}

echo "=========================================="
echo "Phase 5 SLO Verification"
echo "=========================================="
echo "Prometheus URL: ${PROM_URL}"
echo "Output file: ${OUTPUT_FILE}"
echo

mkdir -p reports

# Check for fast burn rate (14.4x threshold)
echo "Checking fast burn rate alerts..."
FAST_BURN=$(curl -s "${PROM_URL}/api/v1/query?query=slo_burn_rate_fast" | jq -r '.data.result | length > 0')

# Check for slow burn rate (6x threshold) 
echo "Checking slow burn rate alerts..."
SLOW_BURN=$(curl -s "${PROM_URL}/api/v1/query?query=slo_burn_rate_slow" | jq -r '.data.result | length > 0')

# Check recovery (success rate back to normal)
echo "Checking recovery status..."
SUCCESS_RATE=$(curl -s "${PROM_URL}/api/v1/query?query=rate(http_requests_total{status=~'2..'}[5m])/rate(http_requests_total[5m])" | jq -r '.data.result[0].value[1] // "0"')
RECOVERY_OK=$(python3 -c "print('true' if float('${SUCCESS_RATE}') > 0.95 else 'false')")

echo "Results:"
echo "  Fast burn triggered: ${FAST_BURN}"
echo "  Slow burn triggered: ${SLOW_BURN}"
echo "  Success rate: ${SUCCESS_RATE}"
echo "  Recovery OK: ${RECOVERY_OK}"

# Generate JSON output
jq -n \
  --argjson fast_burn ${FAST_BURN} \
  --argjson slow_burn ${SLOW_BURN} \
  --arg success_rate "${SUCCESS_RATE}" \
  --argjson recovery_ok ${RECOVERY_OK} \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  '{
    timestamp: $timestamp,
    fast_burn_triggered: $fast_burn,
    slow_burn_triggered: $slow_burn,
    success_rate: ($success_rate | tonumber),
    recovery_ok: $recovery_ok,
    slo_foundation_ok: ($fast_burn and $slow_burn and $recovery_ok)
  }' | tee "${OUTPUT_FILE}"

echo
echo "✅ SLO verification completed"
echo "   Results saved to: ${OUTPUT_FILE}"