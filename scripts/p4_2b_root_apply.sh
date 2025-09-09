#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2b_root_${TS}.md"
echo "# P4-2B Root App Evidence (${TS})" | tee "$R"
sec(){ echo -e "\n## $1\n" | tee -a "$R"; }
run(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; (eval "$@" 2>&1 || true) | sed 's/^/  /' | tee -a "$R"; }

sec "Apply root app"
run kubectl -n argocd apply -f infra/argocd/root/root-app.yaml

sec "List Argo apps"
run kubectl -n argocd get applications -o wide