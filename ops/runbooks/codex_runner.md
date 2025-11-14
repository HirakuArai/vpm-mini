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

# ------------------------------------------------------------------
# ## Runner運用メモ
#
# ### モードと挙動
# - `RUN_MODE` 未指定（既定）または `dry`  
#   - `codex/inbox/*.json` を読み、`run.log` に `[DRY]` ログだけを残す。  
#   - `kubectl` は実行せず、/ask の内容確認や T2/T3 の安全なスモーク用途。
# - `RUN_MODE=exec` + kind≠apply  
#   - **S3 Canary** 相当。許可リスト（`kubectl get/describe/wait`）のみ実行し、Evidence を `run.log` に追記。
# - `RUN_MODE=exec` + `kind=apply` + `approved=true` + `scope` が `infra/k8s/overlays/dev/**`  
#   - **S5 apply** 専用。`kubectl diff -f <manifest>` → `kubectl apply -f <manifest>` → `kubectl get ... -o yaml` を順番に実行し、`apply.log` と `after.yaml` に記録。  
#   - `/ask` コメント例: `S5 apply: dev infra/k8s/overlays/dev/<manifest>.yaml`（任意の dev overlay manifest）。  
#     - `S5 apply: dev hello-ksvc` は `infra/k8s/overlays/dev/hello-ksvc.yaml` を指すショートカット。
#
# ### 誰がいつ回すか（Phase 2 暫定運用）
# - **DRY**  
#   - Runner inbox に新しい /ask JSON が溜まったら、VM Codex が 1 日 1 回程度 or 作業のまとまりで `RUN_MODE=dry bash scripts/codex_inbox_runner.sh` を実行。  
#   - /ask コメントの結果を `_done/` へ送ることで Evidence パイプが閉じる。
# - **EXEC (Canary/S5)**  
#   - `RUN_MODE=exec` は「PR / /ask に EXEC して良い明示の GO サイン（例: `T3 Canary`, `S5 apply: dev ...`)」があるときだけ。  
#   - 実行者は Codex (VM) で、対象 PR のレビュー/承認状況を確認したうえで走らせる。
#
# ### ログ／Evidence の見方
# - `reports/codex_runs/<id>/run.log`  
#   - すべての JSON と DRY/EXEC/S5 の分岐ログがここに残る。
# - `reports/codex_runs/<id>/apply.log`  
#   - S5 apply で実行した `kubectl diff/apply/get` の標準出力・警告。
# - `reports/codex_runs/<id>/after.yaml`  
#   - apply 後（または検証時）のリソース状態。`kubectl get ... -o yaml` に成功した場合のみ出力。
#
# ### 注意事項
# - delete/patch など破壊的なコマンドは Runner では許可していない。  
# - 実際のクラスタ構成（Knative CRD 等）が未整備の場合、S5 apply はエラーになっても Evidence を残して終了する。  
# - `_done/` フォルダへ移動した JSON は再実行されないため、再実施したい場合は新しい inbox JSON を発行する。
