#!/usr/bin/env bash
set -euo pipefail

NS=${NS:-kourier-system}
echo "Port-forwarding 3scale-kourier-gateway (8080:8080) in namespace=${NS}"
kubectl -n "${NS}" port-forward deploy/3scale-kourier-gateway 8080:8080
