# Project Lane bundle templates v1

このドキュメントは Project Lane（黒板SSOT）を更新するための memo bundle テンプレの使い方です。

対象SSOT:
- data/{project_id}/info_nodes_v1.json
- data/{project_id}/info_relations_v1.json

## 作業タイプ
- DocPointer Update: docs/外部URLの「存在・役割・参照先」を黒板に登録する
- Progress Update: 進捗・決定・障害・解決策を黒板に反映する

## テンプレ
- templates/bundles/docpointer_update_bundle_template.yaml
- templates/bundles/progress_update_bundle_template.yaml

## 標準実行（merge runner）
基本は runner で PR まで作る。

```bash
export PR_BOT_TOKEN=...  # 推奨
scripts/info_network/merge_run_v1.sh --project-id {project_id} --bundle <bundle.yaml> --mode pr --policy additive_only
```

- questions が出たら止まる（人間が判断して再実行）
- additive_only を基本にする（supersede/obsoleteで過去方針を壊しにくい）
- run intermediates（snapshot/seed/suggestion）は追跡しない（runnerと.gitignoreが担保）

## DoD
- PRが作られ、CIが通り、mainにマージされる
- 黒板SSOTが更新される
- run artifacts として approved_plan.json と bundle が残る
