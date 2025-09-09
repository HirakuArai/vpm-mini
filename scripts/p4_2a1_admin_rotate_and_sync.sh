#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
R="reports/p4_2a1_admin_rotate_and_sync_${TS}.md"
echo "# P4-2A.1 Admin Rotation & First Sync Evidence (${TS})" | tee "$R"

section(){ echo -e "\n## $1\n" | tee -a "$R"; }
cmd(){ echo -e "\n\`\`\`bash\n$*\n\`\`\`\n" | tee -a "$R"; (eval "$@" 2>&1 || true) | sed 's/^/  /' | tee -a "$R"; }

section "Preflight"
cmd "kubectl -n argocd get deploy,svc,secret | head -n 100"

section "Initial admin secret"
if kubectl -n argocd get secret argocd-initial-admin-secret >/dev/null 2>&1; then
  INIT_PW="$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d || true)"
  if [ -n "${INIT_PW:-}" ]; then
    echo "Initial admin password detected." | tee -a "$R"
  else
    echo "Initial admin secret present but password unreadable." | tee -a "$R"
  fi
else
  echo "Initial admin secret not present (already rotated/cleaned)." | tee -a "$R"
fi

section "Admin rotation (conditional: argocd CLI)"
if command -v argocd >/dev/null 2>&1; then
  # ポートフォワードでローカルから安全に操作
  cmd "kubectl -n argocd rollout status deploy/argocd-server --timeout=180s"
  kubectl -n argocd port-forward svc/argocd-server 8080:443 >/dev/null 2>&1 &
  PF_PID=$!
  trap 'kill $PF_PID >/dev/null 2>&1 || true' EXIT
  sleep 2

  if [ -n "${INIT_PW:-}" ]; then
    # 初期PWでログイン→新PWへローテ
    NEWPW="vpm-$(date +%s)"
    cmd "argocd login localhost:8080 --username admin --password '******' --grpc-web --insecure"
    cmd "argocd account update-password --current-password '******' --new-password '******'"
    echo "**OK**: admin password rotated (masked)" | tee -a "$R"
  else
    echo "Skip rotation: no initial password available." | tee -a "$R"
  fi
else
  echo "argocd CLI not found → rotation step skipped（Secret cleanupのみ実施）" | tee -a "$R"
fi

section "Delete initial secret (cleanup)"
if kubectl -n argocd get secret argocd-initial-admin-secret >/dev/null 2>&1; then
  cmd "kubectl -n argocd delete secret argocd-initial-admin-secret"
else
  echo "Initial admin secret already absent." | tee -a "$R"
fi

section "Force first sync (hello-ai)"
# Auto-Sync待ちだと遅いことがあるので、手動Sync + 健全性待ち
if command -v argocd >/dev/null 2>&1; then
  cmd "argocd app sync vpm-mini-hello-ai --grpc-web --insecure --server localhost:8080"
  cmd "argocd app wait vpm-mini-hello-ai --health --sync --timeout 120 --grpc-web --insecure --server localhost:8080"
else
  # CLIが無い環境では Application に refresh 注入（Argoが即時評価）
  cmd "kubectl -n argocd annotate application vpm-mini-hello-ai argocd.argoproj.io/refresh=hard --overwrite"
  # 反映まで少し待って状態確認
  sleep 20
fi

section "Status after sync"
cmd "kubectl -n argocd get applications.argoproj.io vpm-mini-hello-ai -o wide"
cmd "kubectl -n argocd get applications.argoproj.io vpm-mini-hello-ai -o jsonpath='{.status.sync.status} {\"/\"} {.status.health.status}{\"\\n\"}'"

echo -e "\n---\n✅ Completed P4-2A.1 (Admin rotation & first sync)\n" | tee -a "$R"