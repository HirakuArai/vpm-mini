#!/usr/bin/env bash
#
# Test version of Phase 4 exit verification with mocked kubectl data
#

set -euo pipefail

# Mock kubectl command to return test data
kubectl() {
    if [[ "$*" == "-n argocd get application root-app -o json" ]]; then
        cat /Users/hiraku/projects/vpm-mini/test_kubectl_mock.json
        return 0
    fi
    
    # Fallback to real kubectl for other commands
    command kubectl "$@"
}

export -f kubectl

# Run the actual verification script
bash /Users/hiraku/projects/vpm-mini/scripts/phase4_verify_exit.sh