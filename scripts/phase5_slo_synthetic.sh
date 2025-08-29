#!/usr/bin/env bash
set -euo pipefail

# Phase 5 SLO Synthetic Testing
# Inject 5xx errors and then recovery to trigger fast/slow burn alerts

DURATION_BAD=${DURATION_BAD:-120}   # 2 minutes bad traffic (default)
DURATION_REC=${DURATION_REC:-300}   # 5 minutes recovery (default)
TARGET_URL=${TARGET_URL:-http://localhost:31380}  # Default target

echo "=========================================="
echo "Phase 5 SLO Synthetic Testing"
echo "=========================================="
echo "Bad traffic duration: ${DURATION_BAD}s"
echo "Recovery duration: ${DURATION_REC}s"
echo "Target URL: ${TARGET_URL}"
echo

# Create synthetic load with 5xx errors first
echo "Step 1: Injecting bad traffic for ${DURATION_BAD}s..."
python3 -c "
import requests
import time
import sys
import threading
from datetime import datetime

def make_requests(url, duration, error_rate=0.5):
    start_time = time.time()
    total_requests = 0
    errors = 0
    
    while time.time() - start_time < duration:
        try:
            # Simulate mixed traffic - some good, some bad
            if total_requests % 2 == 0:  # 50% error rate
                # Try to trigger 5xx by overloading or bad requests
                resp = requests.get(url + '/nonexistent', timeout=1)
            else:
                resp = requests.get(url, timeout=1)
            
            total_requests += 1
            if resp.status_code >= 500:
                errors += 1
        except Exception as e:
            errors += 1
            total_requests += 1
        
        time.sleep(0.1)  # 10 RPS
    
    print(f'Bad traffic phase: {total_requests} requests, {errors} errors ({errors/total_requests*100:.1f}%)')

make_requests('${TARGET_URL}', ${DURATION_BAD})
"

echo
echo "Step 2: Recovery phase - good traffic for ${DURATION_REC}s..."
python3 -c "
import requests
import time
from datetime import datetime

def make_good_requests(url, duration):
    start_time = time.time()
    total_requests = 0
    errors = 0
    
    while time.time() - start_time < duration:
        try:
            resp = requests.get(url, timeout=2)
            total_requests += 1
            if resp.status_code >= 400:
                errors += 1
        except Exception as e:
            errors += 1
            total_requests += 1
        
        time.sleep(0.2)  # 5 RPS for recovery
    
    print(f'Recovery phase: {total_requests} requests, {errors} errors ({errors/total_requests*100:.1f}%)')

make_good_requests('${TARGET_URL}', ${DURATION_REC})
"

echo
echo "✅ SLO synthetic testing completed"
echo "   Next: Run phase5_slo_verify.sh to check burn rates"