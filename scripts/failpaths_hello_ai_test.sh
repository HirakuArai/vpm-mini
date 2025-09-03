#!/usr/bin/env bash
set -euo pipefail
NS=${NS:-hyper-swarm}
APP="hello-ai-test"

# Test failure paths against hello-ai-test deployment
OUT_JSON="reports/p2_5_failpaths_$(date +%Y%m%d_%H%M%S).json"
OUT_MD="${OUT_JSON%.json}.md"

# Save current configurations
CUR_AI=$(kubectl -n "$NS" get cm hello-ai-cm -o jsonpath='{.data.AI_ENABLED}')
CUR_MODEL=$(kubectl -n "$NS" get cm hello-ai-cm -o jsonpath='{.data.MODEL}')

# Store results in simple variables
pass=0; total=0

test_case(){
  local name=$1 setup=$2 teardown=$3
  total=$((total+1))
  echo "== case: $name =="
  
  # Setup
  eval "$setup"
  kubectl -n "$NS" rollout restart deployment/hello-ai-test
  kubectl -n "$NS" rollout status deployment/hello-ai-test --timeout=60s
  sleep 2
  
  # Test
  kubectl -n "$NS" port-forward svc/hello-ai-test 8082:8080 >/tmp/pf_test.log 2>&1 &
  local pf=$!
  sleep 2
  
  RESP=$(curl -isS "http://127.0.0.1:8082/hello-ai?msg=ping" 2>/dev/null || true)
  kill $pf 2>/dev/null || true
  
  ST=$(printf "%s" "$RESP" | head -n1 | awk '{print $2}')
  XF=$(printf "%s" "$RESP" | awk -F': ' '/^x-fallback:/{gsub(/\r/,"",$2);print tolower($2)}' | tail -n1)
  
  ok=0
  if [[ "$ST" == "200" && "$XF" == "true" ]]; then 
    ok=1
    pass=$((pass+1))
    echo "✓ PASS: 200 + fallback=true"
  else
    echo "✗ FAIL: status=$ST, fallback=$XF"
  fi
  
  eval "${name}_status='$ST'"
  eval "${name}_fallback='$XF'"
  eval "${name}_ok=$ok"
  
  # Teardown
  eval "$teardown"
}

# Case A: Invalid API key
test_case "invalid_key" \
  'kubectl -n "$NS" delete secret openai-secret --ignore-not-found;
   kubectl -n "$NS" create secret generic openai-secret --from-literal=OPENAI_API_KEY="sk-INVALIDKEY123";  # pragma: allowlist secret
   kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"AI_ENABLED\":\"true\"}}"' \
  'echo "Restoring original secret..."'

# Case B: AI disabled
test_case "ai_disabled" \
  'kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"AI_ENABLED\":\"false\"}}"' \
  'kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"AI_ENABLED\":\"'$CUR_AI'\"}}"'

# Case C: Invalid model
test_case "invalid_model" \
  'kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"MODEL\":\"gpt-unknown-model\",\"AI_ENABLED\":\"true\"}}"' \
  'kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"MODEL\":\"'$CUR_MODEL'\"}}"'

# Restore original secret
echo "Restoring original configurations..."
kubectl -n "$NS" delete secret openai-secret --ignore-not-found
kubectl -n "$NS" create secret generic openai-secret --from-env-file=/Users/hiraku/projects/vpm-mini/.env 2>/dev/null || true
kubectl -n "$NS" patch cm hello-ai-cm --type merge -p "{\"data\":{\"AI_ENABLED\":\"$CUR_AI\"}}"
kubectl -n "$NS" rollout restart deployment/hello-ai-test
kubectl -n "$NS" rollout status deployment/hello-ai-test --timeout=60s

# Generate reports
jq -n \
  --arg ns "$NS" --arg app "$APP" \
  --arg total "$total" --arg passed "$pass" \
  --arg ik_status "${invalid_key_status}" --arg ik_fb "${invalid_key_fallback}" --argjson ik_ok ${invalid_key_ok:-0} \
  --arg ad_status "${ai_disabled_status}" --arg ad_fb "${ai_disabled_fallback}" --argjson ad_ok ${ai_disabled_ok:-0} \
  --arg im_status "${invalid_model_status}" --arg im_fb "${invalid_model_fallback}" --argjson im_ok ${invalid_model_ok:-0} \
  '{
    ns:$ns, app:$app,
    cases:{
      invalid_key:{status:$ik_status, x_fallback:$ik_fb, ok:$ik_ok},
      ai_disabled:{status:$ad_status, x_fallback:$ad_fb, ok:$ad_ok},
      invalid_model:{status:$im_status, x_fallback:$im_fb, ok:$im_ok}
    },
    summary:{total:($total|tonumber), pass:($passed|tonumber)},
    generated_at:(now|todate)
  }' | tee "$OUT_JSON"

cat > "$OUT_MD" <<EOF
# P2-5 Failpaths Evidence

- json: \`$OUT_JSON\`
- summary: pass=$pass / total=$total

## Test Cases
1. **invalid_key**: Invalid OPENAI_API_KEY → expects 200 + fallback=true
2. **ai_disabled**: AI_ENABLED=false → expects 200 + fallback=true  
3. **invalid_model**: Unknown model name → expects 200 + fallback=true

## Results
\`\`\`json
$(cat "$OUT_JSON")
\`\`\`
EOF

echo "$OUT_JSON"