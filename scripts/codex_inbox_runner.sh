#!/usr/bin/env bash
set -euo pipefail

# S3 (non-destructive): execute allowed kubectl (get/describe/wait) with timeouts.
# S1 (DRY) remains default unless RUN_MODE=exec is set.
# Usage: RUN_MODE=exec scripts/codex_inbox_runner.sh

REPO="HirakuArai/vpm-mini"
WORKDIR="$HOME/work/vpm-mini"
INBOX_DIR="codex/inbox"
DONE_DIR="codex/inbox/_done"
RUNS_DIR="reports/codex_runs"
ALLOWED=(get describe wait)
KUBECTL_TIMEOUT=40
RUN_MODE=${RUN_MODE:-dry}   # dry | exec

mkdir -p "$WORKDIR"
cd "$WORKDIR"
mkdir -p "$INBOX_DIR" "$DONE_DIR" "$RUNS_DIR"

# refresh
git fetch origin
git reset --hard origin/main

run_log_line(){ echo "$1" | tee -a "$2"; }
first_real_token(){
  # extract first non-flag token after 'kubectl' (subcmd)
  awk '{skip=0; for(i=1;i<=NF;i++){if($i=="kubectl"){skip=1;continue}; if(skip==1){if($i!~/^-/){print $i; exit}}}}'
}

shopt -s nullglob
for jf in "$INBOX_DIR"/*.json; do
  id=$(basename "$jf" .json)
  outdir="$RUNS_DIR/$id"
  mkdir -p "$outdir"
  log="$outdir/run.log"

  run_log_line "[INFO] Processing $jf (mode=$RUN_MODE)" "$log"
  if command -v jq >/dev/null 2>&1; then
    jq . "$jf" | sed 's/^/[json] /' >> "$log" || true
  fi

  ACTIONS=$(jq -r '.actions[]?.cmd // empty' "$jf" 2>/dev/null || true)
  if [ -z "$ACTIONS" ]; then
    run_log_line "[INFO] no actions; DRY record only" "$log"
  fi

  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    subcmd=$(echo "$cmd" | first_real_token)
    subcmd=${subcmd:-}
    if [[ ! " ${ALLOWED[*]} " == *" ${subcmd} "* ]]; then
      run_log_line "[SKIP] not in allowlist: $cmd" "$log"
      continue
    fi
    if [ "$RUN_MODE" != "exec" ]; then
      run_log_line "[DRY] $cmd" "$log"
      continue
    fi
    run_log_line "[EXEC] $cmd" "$log"
    timeout ${KUBECTL_TIMEOUT}s bash -lc "$cmd" >> "$log" 2>&1 \
      || run_log_line "[WARN] command returned non-zero" "$log"
  done <<< "$ACTIONS"

  # move to _done and push evidence
  git mv -f "$jf" "$DONE_DIR/" || true
  git add -A
  git commit -m "runner(${RUN_MODE}): mark $jf processed; add evidence $outdir" || true
  git push || true

  # optional PR per run (best-effort)
  if command -v gh >/dev/null 2>&1; then
    branch="runner/${RUN_MODE}-$id"
    git checkout -b "$branch" || git checkout "$branch"
    git add -A
    git commit -m "runner(${RUN_MODE}): evidence for $id" || true
    git push -u origin "$branch" || true
    gh pr create -R "$REPO" -t "Runner(${RUN_MODE}): $id evidence" -b "See $RUNS_DIR/$id/run.log" || true
    git switch - || true
    git reset --hard origin/main || true
  fi
done

exit 0
