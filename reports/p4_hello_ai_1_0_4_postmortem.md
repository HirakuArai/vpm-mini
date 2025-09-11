# P4 hello-ai 1.0.4 auto-update — Postmortem

- Timestamp (UTC): 2025-09-11T21:57:46Z
- Changes:
  - GHCR Build v3 (multi-arch amd64/arm64) → tag **1.0.4**
  - Argo CD Image Updater: semver ~1 自動追従で **1.0.3 → 1.0.4**
  - KService image: `ghcr.io/hirakuarai/hello-ai:1.0.4`
- Notes:
  - 1.0.0 の amd64-only digest による ImagePullBackOff を multi-arch 化で解消
  - DoD Enforcer は `skip-dod` ラベルで緊急回避可能な設計に整理
  - Argo App は automated sync (prune/selfHeal) 有効
