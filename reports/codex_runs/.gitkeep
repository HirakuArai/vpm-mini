#!/usr/bin/env bash
set -euo pipefail

REPO="HirakuArai/vpm-mini"
WORKDIR="$HOME/work/vpm-mini"
INBOX_DIR="codex/inbox"
DONE_DIR="codex/inbox/_done"
RUNS_DIR="reports/codex_runs"

mkdir -p "$WORKDIR" 
cd "$WORKDIR"

# Ensure dirs exist in repo
mkdir -p "$INBOX_DIR" "$DONE_DIR" "$RUNS_DIR"

# Always refresh to main
git fetch origin
git reset --hard origin/main

shopt -s nullglob
for jf in "$INBOX_DIR"/*.json; do
  id=$(basename "$jf" .json)
  outdir="$RUNS_DIR/$id"
  mkdir -p "$outdir"
  echo "[DRY] Processing $jf" | tee -a "$outdir/run.log"
  # Pretty-print the JSON into the log for evidence
  if command -v jq >/dev/null 2>&1; then
    jq . "$jf" | sed 's/^/[json] /' >> "$outdir/run.log" || true
  else
    sed 's/^/[json] /' "$jf" >> "$outdir/run.log" || true
  fi
  echo "[DRY] actions[] will be executed in non-dry gate; skipping now" | tee -a "$outdir/run.log"

  # Move json to _done to avoid reprocessing
  git mv -f "$jf" "$DONE_DIR/" || true
  git add -A
  git commit -m "runner(dry): mark $jf processed; add evidence $outdir" || true
  git push || true

  # Open or update a PR with evidence (best-effort)
  if command -v gh >/dev/null 2>&1; then
    branch="runner/dry-$id"
    git checkout -b "$branch" || git checkout "$branch"
    git add -A
    git commit -m "runner(dry): evidence for $id" || true
    git push -u origin "$branch" || true
    gh pr create -R "$REPO" -t "Runner(dry): $id evidence" -b "DRY run; see $RUNS_DIR/$id/run.log" || true
    git switch - || true
    git reset --hard origin/main || true
  fi

done

exit 0
