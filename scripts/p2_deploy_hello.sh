#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports/phase2

echo "## apply" | tee reports/phase2/hello_ready.md
kubectl apply -f infra/k8s/overlays/dev/hello-ksvc.yaml | tee -a reports/phase2/hello_ready.md

echo -e "\n## wait (Ready)" | tee -a reports/phase2/hello_ready.md
kubectl wait ksvc/hello --for=condition=Ready --timeout=90s | tee -a reports/phase2/hello_ready.md || true

echo -e "\n## get ksvc (wide)" | tee -a reports/phase2/hello_ready.md
kubectl get ksvc hello -o wide | tee -a reports/phase2/hello_ready.md || true
