#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2c_monitoring_${TS}.md"
echo "# P4-2C Monitoring App Evidence (${TS})" | tee "$R"
sec(){ echo -e "\n## $1\n" | tee -a "$R"; }
run(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; (eval "$@" 2>&1 || true) | sed 's/^/  /' | tee -a "$R"; }
sec "Apply monitoring app"
run kubectl -n argocd apply -f infra/argocd/apps/monitoring-app.yaml
sec "Argo apps"
run kubectl -n argocd get applications -o wide