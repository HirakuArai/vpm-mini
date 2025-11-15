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
run_apply_sequence(){
  local manifest="$1"
  local outdir="$2"
  local res_name="${3:-hello}"
  local res_ns="${4:-default}"
  local res_kind_cli
  res_kind_cli=$(printf '%s' "${5:-service}" | tr '[:upper:]' '[:lower:]')
  local apply_log="$outdir/apply.log"
  local after_yaml="$outdir/after.yaml"

  mkdir -p "$outdir"
  : > "$apply_log"
  : > "$after_yaml"

  if [ ! -f "$manifest" ]; then
    {
      echo "[ERROR] manifest not found: $manifest"
    } >> "$apply_log"
    return 1
  fi

  {
    echo "[APPLY] manifest=$manifest"
    echo "[APPLY] kubectl diff -f $manifest"
    if kubectl diff -f "$manifest"; then
      echo "[INFO] diff exited 0"
    else
      echo "[WARN] diff returned non-zero"
    fi

    echo "[APPLY] kubectl apply -f $manifest"
    if kubectl apply -f "$manifest"; then
      echo "[INFO] apply exited 0"
    else
      echo "[ERROR] apply returned non-zero"
    fi

    echo "[APPLY] kubectl get ksvc ${res_name} -n ${res_ns} -o yaml"
    if kubectl get ksvc "$res_name" -n "$res_ns" -o yaml | tee "$after_yaml"; then
      echo "[INFO] captured state via ksvc"
    else
      echo "[WARN] kubectl get ksvc failed; falling back to ${res_kind_cli}"
      if kubectl get "$res_kind_cli" "$res_name" -n "$res_ns" -o yaml | tee "$after_yaml"; then
        echo "[INFO] captured state via ${res_kind_cli}"
      else
        echo "[ERROR] failed to capture resource via fallback kind"
      fi
    fi
  } >> "$apply_log" 2>&1
}

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
fi

shopt -s nullglob
for jf in "$INBOX_DIR"/*.json; do
  id=$(basename "$jf" .json)
  outdir="$RUNS_DIR/$id"
  mkdir -p "$outdir"
  log="$outdir/run.log"

  run_log_line "[INFO] Processing $jf (mode=$RUN_MODE)" "$log"
  if [ "$HAS_JQ" -eq 1 ]; then
    jq . "$jf" | sed 's/^/[json] /' >> "$log" || true
  fi

  ACTIONS=""
  kind=""
  approved=""
  scope=""
  action_type=""
  apply_path=""
  apply_res_kind=""
  apply_res_name=""
  apply_res_ns=""
  if [ "$HAS_JQ" -eq 1 ]; then
    ACTIONS=$(jq -r '.actions[]?.cmd // empty' "$jf" 2>/dev/null || true)
    kind=$(jq -r '.kind // ""' "$jf" 2>/dev/null || echo "")
    approved=$(jq -r '.approved // ""' "$jf" 2>/dev/null || echo "")
    scope=$(jq -r '.scope // ""' "$jf" 2>/dev/null || echo "")
    action_type=$(jq -r '.actions[0].type // ""' "$jf" 2>/dev/null || echo "")
    apply_path=$(jq -r '.actions[0].path // ""' "$jf" 2>/dev/null || echo "")
    apply_res_kind=$(jq -r '.actions[0].resource.kind // ""' "$jf" 2>/dev/null || echo "")
    apply_res_name=$(jq -r '.actions[0].resource.name // ""' "$jf" 2>/dev/null || echo "")
    apply_res_ns=$(jq -r '.actions[0].resource.namespace // ""' "$jf" 2>/dev/null || echo "")
  fi

  handled_apply=0
  manifest="${apply_path:-$scope}"
  if [ "$RUN_MODE" = "exec" ] && [ "$HAS_JQ" -eq 1 ] && [ "$kind" = "apply" ] && [ "$approved" = "true" ] && [ "$action_type" = "k8s-apply" ] && [[ "$scope" == infra/k8s/overlays/dev/* ]]; then
    manifest=${manifest:-infra/k8s/overlays/dev/hello-ksvc.yaml}
    run_log_line "[INFO] Triggering S5 apply manifest=$manifest" "$log"
    run_apply_sequence "$manifest" "$outdir" "${apply_res_name:-hello}" "${apply_res_ns:-default}" "${apply_res_kind:-service}"
    run_log_line "[INFO] S5 apply artifacts: $outdir/apply.log, $outdir/after.yaml" "$log"
    handled_apply=1
  fi

  if [ "$handled_apply" -eq 0 ] && [ -z "$ACTIONS" ]; then
    run_log_line "[INFO] no actions; DRY record only" "$log"
  fi

  if [ "$handled_apply" -eq 0 ]; then
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
  fi

  # move to _done and push evidence (dry-only)
  if [ "$RUN_MODE" = "exec" ]; then
    mv -f "$jf" "$DONE_DIR/" || true
  else
    git mv -f "$jf" "$DONE_DIR/" || true
    git add -A
    git commit -m "runner(${RUN_MODE}): mark $jf processed; add evidence $outdir" || true
    git push || true
  fi

  # optional PR per run (best-effort)
  if [ "$RUN_MODE" != "exec" ] && command -v gh >/dev/null 2>&1; then
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

if [ "$RUN_MODE" = "exec" ]; then
  echo "[WARN] RUN_MODE=exec: main への自動 push は無効化中です。今回の evidence はローカル (reports/codex_runs/**) のみに保存されました。"
fi

exit 0
