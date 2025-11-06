# devbox Codex — 運用約束（最小）

- 実行器は devbox のみ。Atlas（OpenAIエージェントブラウザ）は **UI補助**（Cloud Shell 操作・GitHub設定）専用。
- トリガ: GitHub Issue に **/codex run {JSON}** を投稿し、**Approve** ラベルを付与。さらに **codex:queued** ラベルが必要。
- デデュープ: 同一コメントは無視（comment本文のSHA256）。
- 成功: **PRは常に1つだけ**、`reports/` に成果物、PR本文とIssueに要約。
- 失敗: **PRは起こさず** Issueに要約を返す（エラーメッセージは先頭180文字まで）。
- 権限: PATは fine-grained（contents+pull_requests+issues）。将来 GitHub App 化。
