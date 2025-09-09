#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
RPT="reports/p4_0_preflight_${TS}.md"
echo "# P4-0 Preflight Evidence (${TS})" | tee "$RPT"

section(){ echo -e "\n## $1\n" | tee -a "$RPT"; }
run(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$RPT"; eval "$@" 2>&1 | sed 's/^/  /' | tee -a "$RPT"; }

FAIL=0
note_fail(){ echo -e "\n**NG**: $1" | tee -a "$RPT"; FAIL=1; }
ok(){ echo -e "\n**OK**: $1" | tee -a "$RPT"; }

section "kubectl context & nodes"
if run "kubectl cluster-info" && run "kubectl get nodes -o wide"; then ok "k8s reachable"; else note_fail "kubectl not connected"; fi

section "Knative/kourier health (optional but recommended)"
if run "kubectl -n knative-serving get deploy"; then
  if run "kubectl -n kourier-system get deploy"; then ok "knative/kourier present"; fi
else
  echo "Knative not detected; hello-ai may still sync if not required." | tee -a "$RPT"
fi

section "Target namespace check"
if run "kubectl get ns hyper-swarm"; then ok "namespace exists"; else ok "namespace will be created via CreateNamespace=true"; fi

section "GitOps path existence"
if [ -d infra/k8s/overlays/dev/hello ]; then ok "path exists: infra/k8s/overlays/dev/hello"; else note_fail "missing path: infra/k8s/overlays/dev/hello"; fi

section "Kustomize dry-run (if kustomization exists)"
if [ -f infra/k8s/overlays/dev/hello/kustomization.yaml ]; then
  if run "kubectl apply --dry-run=client -k infra/k8s/overlays/dev/hello"; then ok "kustomize dry-run passed"; else note_fail "kustomize dry-run failed"; fi
else
  echo "No kustomization.yaml; skipping dry-run." | tee -a "$RPT"
fi

section "git working tree"
if [ -z "$(git status --porcelain)" ]; then ok "clean working tree"; else note_fail "uncommitted changes exist"; fi

section "Docker/Container runtime"
if command -v docker >/dev/null 2>&1; then
  if run "docker info >/dev/null"; then ok "docker running"; else note_fail "docker not running"; fi
else
  echo "docker CLI not found; assuming external k8s." | tee -a "$RPT"
fi

section "GitHub reachability (for ArgoCD repo access)"
if run "git ls-remote --heads https://github.com/HirakuArai/vpm-mini.git | head -n1"; then ok "GitHub reachable"; else note_fail "GitHub not reachable"; fi

echo -e "\n---" | tee -a "$RPT"
if [ "$FAIL" -eq 0 ]; then
  echo "✅ PREVIEW: All checks GREEN. Proceed to P4-1 Seed." | tee -a "$RPT"
  exit 0
else
  echo "❌ PREVIEW: Preflight has NG items. Stop before seeding." | tee -a "$RPT"
  exit 2
fi