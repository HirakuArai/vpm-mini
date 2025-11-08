# devbox VM (GCE)
- Project: vpm-mini-prod
- Zone: asia-northeast1-b
- Name: devbox-codex
- Provisioning: GitHub Actions (provision_devbox.yml, WIF)
- After create:
  1) SSH: `gcloud compute ssh devbox-codex --zone=asia-northeast1-b`
  2) Bootstrap: `curl -fsSL https://raw.githubusercontent.com/HirakuArai/vpm-mini/main/scripts/devbox_bootstrap.sh | bash`
  3) Paste Fine-grained PAT (Contents/Issues/PR: R/W for HirakuArai/vpm-mini)
  4) Verify: `systemctl --user status codex-worker`
