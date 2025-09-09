#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2d_notifications_${TS}.md"
echo "# P4-2D Notifications Evidence (${TS})" | tee "$R"
sec(){ echo -e "\n## $1\n" | tee -a "$R"; }
run(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; (eval "$@" 2>&1 || true) | sed 's/^/  /' | tee -a "$R"; }

sec "Apply notifications configmap"
run kubectl -n argocd apply -f infra/argocd/notifications/configmap.yaml
sec "Check notifications controller"
run kubectl -n argocd get deploy argocd-notifications-controller -o wide
run kubectl -n argocd logs deploy/argocd-notifications-controller --tail=200

sec "Stimulate OutOfSync (annotate hello-ai)"
run kubectl -n argocd annotate application vpm-mini-hello-ai argocd.argoproj.io/refresh=hard --overwrite
sleep 10
sec "Controller logs after refresh"
run kubectl -n argocd logs deploy/argocd-notifications-controller --tail=200

echo -e "\n---\n✅ Completed P4-2D (Notifications minimal)\n" | tee -a "$R"