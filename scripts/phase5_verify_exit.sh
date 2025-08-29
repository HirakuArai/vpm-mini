#!/usr/bin/env bash
set -euo pipefail

# 期待ファイル（存在しない場合は false とみなす）
SLO_JSON=${SLO_JSON:-reports/phase5_slo_verify.json}
CANARY_JSON=${CANARY_JSON:-reports/phase4_canary_promotion.json}
GUARD_JSON=${GUARD_JSON:-reports/phase5_cd_guard_result.json}
APPSET_JSON=${APPSET_JSON:-reports/phase5_appset_verify.json}
FAIL_JSON=${FAIL_JSON:-reports/phase5_failover_result.json}
FREEZE_FILE=${FREEZE_FILE:-.ops/deploy_freeze.json}

jqtrue () { # $1=file $2=jq-expr → true/false
  [ -f "$1" ] || { echo false; return; }
  val=$(jq -re "$2" "$1" 2>/dev/null || echo "")
  [ "$val" = "true" ] && echo true || echo false
}

echo "=========================================="
echo "Phase 5 Exit Comprehensive Verification"
echo "=========================================="
echo

echo "Checking individual components..."

# --- 個別判定 ---
echo "1. SLO Foundation (Fast/Slow burn + Recovery)..."
SLO_OK=$(jqtrue "$SLO_JSON" '.fast_burn_triggered and .slow_burn_triggered and .recovery_ok')
echo "   File: $SLO_JSON"
echo "   Status: $SLO_OK"
if [ "$SLO_OK" = "false" ]; then
    echo "   Details: Missing or incomplete SLO burn rate testing"
fi
echo

echo "2. CD Canary Promotion (90→50→100)..."
CANARY_OK=$(jqtrue "$CANARY_JSON" '(."90:10".gate_ok // false) and (."50:50".gate_ok // false) and (."100:0".final_ok // false)')
echo "   File: $CANARY_JSON"
echo "   Status: $CANARY_OK"
if [ "$CANARY_OK" = "false" ]; then
    echo "   Details: Missing or incomplete canary promotion gates"
fi
echo

echo "3. Post-Promotion Guard + Freeze Status..."
GUARD_OK=$(jqtrue "$GUARD_JSON" '.guard_ok')
FREEZE_OFF=true
if [ -f "$FREEZE_FILE" ]; then
  FREEZE_OFF=$(jq -re '.freeze==false' "$FREEZE_FILE" 2>/dev/null || echo false)
  echo "   Freeze file exists: $FREEZE_FILE"
  echo "   Freeze status: $(jq -r '.freeze // "unknown"' "$FREEZE_FILE" 2>/dev/null || echo "parse error")"
else
  echo "   Freeze file: Not found (OK)"
fi
GUARD_ALL=$([ "$GUARD_OK" = true ] && [ "$FREEZE_OFF" = true ] && echo true || echo false)
echo "   Guard file: $GUARD_JSON"
echo "   Guard OK: $GUARD_OK"
echo "   Freeze OFF: $FREEZE_OFF"
echo "   Combined Status: $GUARD_ALL"
echo

echo "4. Multi-Cluster GitOps (ApplicationSet)..."
APPSET_OK=$(jqtrue "$APPSET_JSON" '.synced and .healthy and .a_http_200 and .b_http_200')
echo "   File: $APPSET_JSON"
echo "   Status: $APPSET_OK"
if [ "$APPSET_OK" = "false" ]; then
    echo "   Details: Missing or incomplete multi-cluster synchronization"
fi
echo

echo "5. Failover Drill (RTO≤60, SR≥95%, P50<1000)..."
FAILOVER_OK=$(jqtrue "$FAIL_JSON" '.all_ok')
echo "   File: $FAIL_JSON"
echo "   Status: $FAILOVER_OK"
if [ "$FAILOVER_OK" = "false" ]; then
    echo "   Details: Missing or incomplete failover validation"
fi
echo

# Overall assessment
ALL_OK=$([ "$SLO_OK" = true ] && [ "$CANARY_OK" = true ] && [ "$GUARD_ALL" = true ] && [ "$APPSET_OK" = true ] && [ "$FAILOVER_OK" = true ] && echo true || echo false)

echo "=========================================="
echo "Overall Assessment: $ALL_OK"
echo "=========================================="

# 出力
OUT=reports/phase5_exit_result.json
mkdir -p reports
jq -n \
  --argjson slo $([ "$SLO_OK" = true ] && echo true || echo false) \
  --argjson canary $([ "$CANARY_OK" = true ] && echo true || echo false) \
  --argjson guard $([ "$GUARD_ALL" = true ] && echo true || echo false) \
  --argjson appset $([ "$APPSET_OK" = true ] && echo true || echo false) \
  --argjson failover $([ "$FAILOVER_OK" = true ] && echo true || echo false) \
  --arg freeze_file $([ -f "$FREEZE_FILE" ] && echo "$FREEZE_FILE" || echo "N/A") \
  --argjson all $([ "$ALL_OK" = true ] && echo true || echo false) \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg commit "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)" \
  '{
     timestamp: $timestamp,
     commit: $commit,
     components: {
       slo_foundation: $slo,
       canary_promotion: $canary,
       post_promotion_guard: $guard,
       multicluster_gitops: $appset,
       failover_drill: $failover
     },
     freeze_file: $freeze_file,
     phase5_complete: $all,
     details: {
       slo_file: "'$SLO_JSON'",
       canary_file: "'$CANARY_JSON'", 
       guard_file: "'$GUARD_JSON'",
       appset_file: "'$APPSET_JSON'",
       failover_file: "'$FAIL_JSON'"
     }
   }' | tee "$OUT"

echo
echo "Results saved to: $OUT"

# スナップショット md 生成
SNAP=reports/snap_phase5-complete.md
DATE_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ"); COMMIT=$(git rev-parse --short HEAD)
sed -e "s|{{DATE}}|$DATE_ISO|g" \
    -e "s|{{COMMIT}}|$COMMIT|g" \
    -e "s|{{RESULT_JSON}}|$OUT|g" \
    reports/templates/phase5_exit_checklist.md.tmpl > "$SNAP"

echo "Snapshot generated: $SNAP"
echo

# 終了コード
if [ "$ALL_OK" = true ]; then
    echo "🎉 [SUCCESS] Phase 5 Exit - All Green!"
    echo "   All components verified successfully"
    echo "   Ready for phase5-complete tag"
    exit 0
else
    echo "❌ [FAILURE] Phase 5 Exit - Not All Green"
    echo "   Please review failed components above"
    echo "   Fix issues before proceeding to Phase 6"
    exit 1
fi