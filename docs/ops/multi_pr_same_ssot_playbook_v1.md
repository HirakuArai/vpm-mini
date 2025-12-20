# Multi-PR on same SSOT playbook v1

同一SSOT（例：data/{project_id}/info_nodes_v1.json）を複数PRで並行更新する際の運用。

## 原則
- 同じファイルを複数PRで触るなら、先行PRを先にマージする
- 後続PRは origin/main を取り込んでから（rebase推奨）マージする
- 競合が出たら「どちらが最新の決定か」「重複decisionはdropか」を先に判断して解消

## 推奨フロー
1. PR-A を先にマージ
2. PR-B のブランチで main 追随
   - git fetch origin --prune
   - git rebase origin/main
3. CIが通ることを確認して PR-B をマージ

## よくある事故と回避
- required checks が Expected のまま：PR作成がGITHUB_TOKEN起点 → PAT（PR_BOT_TOKEN）推奨
- run intermediates をコミット：runner/.gitignoreで防止（#977）
