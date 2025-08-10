# VPM-mini: Project Operation Rules (Strict)

## Branch / Commit / PR
- 1タスク=1ブランチ=1目的。命名: <type>/<slug> 例) chore/ci-artifacts, feat/summary-pipeline
- main直pushは原則禁止（ALLOW_MAIN_PUSH=1 の明示許可がある時のみ）。
- コミットは小さく、`type: subject`（例: chore: add DoD link section）
- すべてのPRは `.github/pull_request_template.md` を使用。「完了条件（DoD）」欄にProjectsノートURL必須。

## Preflight（開始前）
- `git status` がクリーンでない場合は `git stash -u -m "temp"`。
- `STATE/current_state.md` と `diagrams/src/*.md` が存在。
- `.gitignore` に `diagrams/export/` を含める。

## File Policy
- 図は `diagrams/src/*.md` を唯一の真実。`diagrams/export/*.svg` はコミットしない。
- CI設定は `.github/workflows/ci.yml` に集約。

## Execution Guard
- 破壊的操作（reset --hard / push -f）禁止。必要時は事前承認。
- 進行は Plan → Confirm → Run → Report（各段階で停止点を設ける）。

## Staging / Review Rules
- 目的外差分はステージ禁止。`git status` / `git diff` を提示し承認を得る。
- コミット前に `git diff --staged` を提示し承認を得る。
- PR作成後、Actions の Run URL と Artifacts リンクを PR本文の Evidence に追記。

## After Merge
- `STATE/current_state.md` を更新（今日の変更／次アクション）。
- `diagrams/src/ops_single_source_of_truth_v1.md` の class を必要に応じて更新（SVGは生成のみでコミットしない）。
