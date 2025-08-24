#!/bin/bash
set -euo pipefail

BR=feat/p1-s02-dockerize-roles
PR_TITLE="feat(p1-s02): dockerize 5 roles with compose hello tour"
PR_BODY='### Summary
- Add `docker/Dockerfile.base` & `docker/Dockerfile.app`
- Add `compose.yaml` (watcher/curator/planner/synthesizer/archivist)  
- Implement `--hello` in `playground.py` to print one-line self-intro per role

### DoD
- [x] `make compose-up && make compose-logs` shows **hello** for all 5 roles
- [x] Evidence saved in `reports/s2_*`

### Evidence
- `reports/s2_compose_hello.log`
- `reports/s2_compose_ps.txt`
- `reports/s2_hello_exit.code` (= 0)'

# 0) gh authentication check
if ! command -v gh >/dev/null 2>&1; then
  echo "[ERROR] GitHub CLI (gh) not found. Please install and retry."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  if [ -n "${GH_TOKEN:-}" ]; then
    echo "[INFO] Using GH_TOKEN for authentication"
    echo "$GH_TOKEN" | gh auth login --with-token
  else
    echo "[INFO] Starting device authentication flow"
    echo "Please complete authentication in your browser"
    gh auth login -h github.com -p https -w
  fi
  gh auth setup-git || true
fi

# 1) Check current branch
echo "[INFO] Current branch: $(git rev-parse --abbrev-ref HEAD)"

# 2) Create PR or reuse existing
if gh pr view "$BR" >/dev/null 2>&1; then
  echo "[INFO] PR already exists for branch $BR"
  PR_URL=$(gh pr view "$BR" --json url -q .url)
else
  echo "[INFO] Creating new PR"
  gh pr create --head "$BR" --title "$PR_TITLE" --body "$PR_BODY"
  PR_URL=$(gh pr view "$BR" --json url -q .url)
fi

# 3) Add labels
echo "[INFO] Adding labels: phase1, docker, infra"
gh pr edit "$BR" --add-label phase1 --add-label docker --add-label infra

# 4) Enable auto-merge (squash)
echo "[INFO] Enabling auto-merge (squash)"
gh pr merge "$BR" --auto --squash

# 5) Show status
echo ""
echo "==================== PR Status ===================="
gh pr view "$BR" --json url,state,isDraft,mergeStateStatus,labels -q \
  '"PR URL: " + .url + "\nState: " + .state + "\nMerge State: " + .mergeStateStatus + "\nLabels: " + ( [ .labels[].name ] | join(", ") )'
echo "===================================================="
echo ""
echo "✅ PR created successfully!"
echo "   Once CI checks pass, it will be automatically merged (squash)."