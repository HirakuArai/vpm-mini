#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2a_hardening_${TS}.md"
echo "# P4-2A Argo CD Hardening Evidence (${TS})" | tee "$R"
section(){ echo -e "\n## $1\n" | tee -a "$R"; }
cmd(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; eval "$@" 2>&1 | sed 's/^/  /' | tee -a "$R"; }

section "Apply Project"
cmd kubectl -n argocd apply -f infra/argocd/projects/vpm-mini-dev.yaml

section "Patch hello-ai app to project=vpm-mini-dev"
cmd kubectl -n argocd apply -f infra/argocd/apps/hello-ai-app.yaml

section "List Applications status"
cmd kubectl -n argocd get applications.argoproj.io -o wide

section "Admin initial secret check"
if kubectl -n argocd get secret argocd-initial-admin-secret >/dev/null 2>&1; then
  echo "Initial admin secret still exists. Consider rotating admin password and then deleting the initial secret." | tee -a "$R"
else
  echo "Initial admin secret not present (OK)" | tee -a "$R"
fi