#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2e_image_updater_${TS}.md"
echo "# P4-2E Image Updater Placeholder Evidence (${TS})" | tee "$R"
sec(){ echo -e "\n## $1\n" | tee -a "$R"; }
run(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; (eval "$@" 2>&1 || true) | sed 's/^/  /' | tee -a "$R"; }
sec "Apply app"
run kubectl -n argocd apply -f infra/argocd/apps/image-updater.yaml
sec "Apps list"
run kubectl -n argocd get applications -o wide
echo -e "\n---\n✅ Completed P4-2E (Image Updater placeholder)\n" | tee -a "$R"