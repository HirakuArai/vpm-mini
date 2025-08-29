#!/usr/bin/env bash
set -euo pipefail

# Phase 4 Canary Promotion Simulation
# HTTPRoute progression: 90:10 → 50:50 → 100:0 with SLO gate validation

N=${N:-300}  # Number of requests per stage (can be shortened for dev)
TARGET_URL=${TARGET_URL:-http://localhost:31380}
OUTPUT_FILE=${OUTPUT_FILE:-reports/phase4_canary_promotion.json}

echo "=========================================="
echo "Phase 4 Canary Promotion Simulation"
echo "=========================================="
echo "Requests per stage: ${N}"
echo "Target URL: ${TARGET_URL}"
echo "Output file: ${OUTPUT_FILE}"
echo

mkdir -p reports

# Simulate canary promotion stages
simulate_stage() {
  local stage=$1
  local requests=$2
  local url=$3
  
  echo "Stage ${stage}: Testing with ${requests} requests..."
  
  python3 -c "
import requests
import time
import json
from statistics import mean

def test_stage(url, requests):
    start_time = time.time()
    response_times = []
    success_count = 0
    
    for i in range(requests):
        try:
            resp_start = time.time()
            resp = requests.get(url, timeout=5)
            resp_time = (time.time() - resp_start) * 1000
            response_times.append(resp_time)
            
            if resp.status_code < 400:
                success_count += 1
        except Exception as e:
            response_times.append(5000)  # Timeout
        
        if i % 50 == 0:
            print(f'  Progress: {i}/{requests}', flush=True)
        time.sleep(0.01)  # Small delay
    
    end_time = time.time()
    duration = end_time - start_time
    success_rate = success_count / requests
    avg_latency = mean(response_times) if response_times else 0
    p50_latency = sorted(response_times)[len(response_times)//2] if response_times else 0
    
    print(f'  Duration: {duration:.1f}s')
    print(f'  Success rate: {success_rate:.3f}')
    print(f'  Avg latency: {avg_latency:.1f}ms')
    print(f'  P50 latency: {p50_latency:.1f}ms')
    
    # SLO gate check (success_rate >= 0.95, p50 < 1000ms)
    gate_ok = success_rate >= 0.95 and p50_latency < 1000
    
    return {
        'duration_sec': duration,
        'success_rate': success_rate,
        'avg_latency_ms': avg_latency,
        'p50_latency_ms': p50_latency,
        'gate_ok': gate_ok
    }

result = test_stage('${url}', ${requests})
print(json.dumps(result, indent=2))
" > /tmp/stage_${stage///:/_}_result.json

  cat /tmp/stage_${stage///:/_}_result.json
}

echo
echo "=== Stage 1: 90:10 Canary ==="
STAGE1_RESULT=$(simulate_stage "90:10" $N $TARGET_URL)

echo
echo "=== Stage 2: 50:50 Canary ==="
STAGE2_RESULT=$(simulate_stage "50:50" $N $TARGET_URL)

echo  
echo "=== Stage 3: 100:0 Final ==="
STAGE3_RESULT=$(simulate_stage "100:0" $N $TARGET_URL)

# Combine results
echo
echo "Combining results..."
jq -n \
  --argjson stage1 "$(cat /tmp/stage_90_10_result.json)" \
  --argjson stage2 "$(cat /tmp/stage_50_50_result.json)" \
  --argjson stage3 "$(cat /tmp/stage_100_0_result.json)" \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  '{
    timestamp: $timestamp,
    "90:10": $stage1,
    "50:50": $stage2, 
    "100:0": ($stage3 | . + {final_ok: .gate_ok}),
    overall_ok: ($stage1.gate_ok and $stage2.gate_ok and $stage3.gate_ok)
  }' | tee "${OUTPUT_FILE}"

# Cleanup temp files
rm -f /tmp/stage_*_result.json

echo
echo "✅ Canary promotion simulation completed"
echo "   Results saved to: ${OUTPUT_FILE}"