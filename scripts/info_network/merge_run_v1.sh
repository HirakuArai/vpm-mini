#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
merge_run_v1.sh - Generic info_network update-cycle runner
Usage:
  scripts/info_network/merge_run_v1.sh \
    --project-id <id> \
    --bundle <path/to/bundle.yaml> \
    [--model gpt-4.1] \
    [--mode dry-run|apply|pr] \
    [--policy additive_only] \
    [--drop-add-id-contains <substr>]... \
    [--drop-add-id-regex <regex>]... \
    [--run-dir <dir>] \
    [--env <path/to/.env>]

Behavior:
- Loads OpenAI env (.env or --env; fallback: /Users/hiraku/projects/vpm-mini/.env)
- Auto-stashes dirty working tree to avoid mixing
- Creates run_dir (default: reports/<project>/runs/<timestamp>)
- Runs: run_update_cycle_v1_1.py
- Questions gate:
  - dry-run: stops after suggestion
  - apply/pr: stops if questions>0
- apply: approve+apply (no commit)
- pr: approve+apply + commit + push + open PR (uses PR_BOT_TOKEN if set)
EOF
}

die(){ echo "ERROR: $*" >&2; exit 1; }

PROJECT_ID=""
BUNDLE=""
MODEL="gpt-4.1"
MODE="dry-run"
POLICY=""
RUN_DIR=""
ENV_PATH=""
DROP_CONTAINS=()
DROP_REGEX=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id) PROJECT_ID="${2:-}"; shift 2;;
    --bundle) BUNDLE="${2:-}"; shift 2;;
    --model) MODEL="${2:-}"; shift 2;;
    --mode) MODE="${2:-}"; shift 2;;
    --policy) POLICY="${2:-}"; shift 2;;
    --run-dir) RUN_DIR="${2:-}"; shift 2;;
    --env) ENV_PATH="${2:-}"; shift 2;;
    --drop-add-id-contains) DROP_CONTAINS+=("${2:-}"); shift 2;;
    --drop-add-id-regex) DROP_REGEX+=("${2:-}"); shift 2;;
    -h|--help) usage; exit 0;;
    *) die "unknown arg: $1";;
  esac
done

[[ -n "$PROJECT_ID" ]] || die "--project-id is required"
[[ -n "$BUNDLE" ]] || die "--bundle is required"
[[ -f "$BUNDLE" ]] || die "bundle not found: $BUNDLE"

case "$MODE" in
  dry-run|apply|pr) ;;
  *) die "--mode must be dry-run|apply|pr (got: $MODE)";;
esac

load_env() {
  local p=""
  if [[ -n "$ENV_PATH" ]]; then
    p="$ENV_PATH"
  elif [[ -f ".env" ]]; then
    p=".env"
  elif [[ -f "/Users/hiraku/projects/vpm-mini/.env" ]]; then
    p="/Users/hiraku/projects/vpm-mini/.env"
  fi
  [[ -n "$p" ]] || die ".env not found. Provide --env /path/to/.env"
  set -a
  source "$p"
  set +a
  python - <<PY
import os
v=os.getenv("OPENAI_API_KEY","")
print("OPENAI_API_KEY present:", bool(v), "prefix:", (v[:3] if v else ""))
assert v, "OPENAI_API_KEY missing"
PY
}

auto_stash() {
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree dirty -> stashing to avoid mixing..."
    git stash push -u -m "auto-stash: merge_run_v1 $(date +%Y%m%d-%H%M%S)" || true
  fi
}

ts_utc() { date -u +%Y%m%d-%H%M%S; }

if [[ -z "$RUN_DIR" ]]; then
  RUN_DIR="reports/${PROJECT_ID}/runs/$(ts_utc)"
fi
mkdir -p "$RUN_DIR"

load_env
auto_stash

echo "=== run_update_cycle_v1_1 ==="
python tools/info_network/run_update_cycle_v1_1.py \
  --bundle "$BUNDLE" \
  --project-id "$PROJECT_ID" \
  --model "$MODEL" \
  --run-dir "$RUN_DIR"

SUGG="${RUN_DIR}/suggestion_plan_v1_1.json"
[[ -f "$SUGG" ]] || die "missing suggestion plan: $SUGG"

echo "=== suggestion stats ==="
python - <<PY
import json
d=json.load(open("${SUGG}","r",encoding="utf-8"))
qs=d.get("questions",[]) or []
print("run_dir:", "${RUN_DIR}")
print("questions:", len(qs))
print("add:", len(d.get("add",[]) or []),
      "update:", len(d.get("update",[]) or []),
      "supersedes:", len(d.get("supersedes",[]) or []),
      "obsolete:", len(d.get("obsolete",[]) or []))
if qs:
  for i,q in enumerate(qs,1):
    print(f"[Q{i}] about_new={q.get('about_new')} :: {q.get('question')}")
PY

if [[ "$MODE" == "dry-run" ]]; then
  echo "MODE=dry-run -> stop here. Suggestion at: $SUGG"
  exit 0
fi

QCOUNT="$(python - <<PY
import json
d=json.load(open("${SUGG}","r",encoding="utf-8"))
print(len(d.get("questions",[]) or []))
PY
)"
if [[ "$QCOUNT" != "0" ]]; then
  echo "STOP: questions exist ($QCOUNT)."
  exit 2
fi

APPROVED="${RUN_DIR}/approved_plan.json"
echo "=== approve ==="
python tools/info_network/approve_update_plan_v1.py \
  --input "$SUGG" \
  --output "$APPROVED" \
  --mode approve

PATCH_ARGS=()
if [[ "$POLICY" == "additive_only" ]]; then
  PATCH_ARGS+=(--additive-only)
fi
for s in "${DROP_CONTAINS[@]:-}"; do
  [[ -n "$s" ]] && PATCH_ARGS+=(--drop-add-id-contains "$s")
done
for r in "${DROP_REGEX[@]:-}"; do
  [[ -n "$r" ]] && PATCH_ARGS+=(--drop-add-id-regex "$r")
done

if [[ "${#PATCH_ARGS[@]}" -gt 0 ]]; then
  echo "=== patch approved plan ==="
  python tools/info_network/plan_policy_patch_v1.py --plan "$APPROVED" "${PATCH_ARGS[@]}"
fi

echo "=== apply ==="
python tools/info_network/apply_info_update_plan_v1.py \
  --plan "$APPROVED" \
  --nodes "data/${PROJECT_ID}/info_nodes_v1.json" \
  --relations "data/${PROJECT_ID}/info_relations_v1.json"

echo "=== validate JSON ==="
python -m json.tool "data/${PROJECT_ID}/info_nodes_v1.json" > /dev/null
python -m json.tool "data/${PROJECT_ID}/info_relations_v1.json" > /dev/null
echo "OK: json.tool"

if [[ "$MODE" == "apply" ]]; then
  echo "MODE=apply -> done (no commit). Run dir: $RUN_DIR"
  exit 0
fi

echo "=== MODE=pr: commit + PR ==="
CUR="$(git branch --show-current)"
if [[ "$CUR" == "main" ]]; then
  SAFE="$(basename "$BUNDLE" | sed 's/[^A-Za-z0-9._-]/_/g')"
  BR="auto/${PROJECT_ID}/merge/${SAFE}-$(ts_utc)"
  git switch -c "$BR"
else
  BR="$CUR"
fi

git add \
  "data/${PROJECT_ID}/info_nodes_v1.json" \
  "data/${PROJECT_ID}/info_relations_v1.json" \
  "$APPROVED" \
  "${RUN_DIR}"/*bundle*.yaml || true
git add docs || true

# Safety: never stage heavy run intermediates even if they slip through
git reset -q -- "${RUN_DIR}/snapshot_raw.json" "${RUN_DIR}/seed_plan_"*".json" "${RUN_DIR}/suggestion_plan_"*".json" 2>/dev/null || true

git commit -m "data(${PROJECT_ID}): merge update cycle ($(basename "$BUNDLE"))" || { echo "Nothing to commit."; exit 0; }

if [[ -n "${PR_BOT_TOKEN:-}" ]]; then
  echo "PR_BOT_TOKEN present -> using it for push/PR"
  git remote set-url origin "https://x-access-token:${PR_BOT_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
  export GH_TOKEN="$PR_BOT_TOKEN"
else
  echo "WARNING: PR_BOT_TOKEN not set; required checks may stall when using the default GitHub token."
fi

git push -u origin "$BR"

if command -v gh >/dev/null 2>&1; then
  PR_URL="$(gh pr create --base main --head "$BR" -t "data(${PROJECT_ID}): merge update" -b "Run: ${RUN_DIR}")" || true
  if [[ -n "${PR_URL:-}" ]]; then
    echo "PR: $PR_URL"
    gh pr view --web || true
  else
    echo "gh pr create failed (maybe PR already exists)."
    gh pr view --web || true
  fi
else
  echo "gh CLI not found. Create PR manually for branch: $BR"
fi

echo "DONE. Run dir: $RUN_DIR"
