# hakone-e2: 更新エンジン方式・構成（engine_design）v1

## 目的
Deep Research / メモ / 既存データなどの入力（bundle）から、hakone-e2 の canonical（nodes/relations）を
「propose → questions → approve → apply」で安全に更新し続けられる形にする。

## 入力単位（bundle）
- 単位: `info_source_bundle_v1`
- 最小要素:
  - project_id, source_type, source_id, title, time_range, raw_text
- bundle は run dir（reports/hakone-e2/runs/<timestamp>/）配下に保存し、入力と出力を同じ箱にまとめる

## SSOT（canonical）
- SSOT は `data/hakone-e2/` の2ファイル
  - info_nodes_v1.json
  - info_relations_v1.json

## 更新サイクル（安全装置つき）
1. bundle作成（raw_text + hints）
2. update cycle 実行（bundle→snapshot→seed→suggestion）
3. questions 判定
   - questions > 0: 停止して人間が回答（approve/applyしない）
   - questions == 0: approve→apply
4. apply 後に json妥当性・整合性チェック（id重複/endpoint欠損など）
5. PR化して main に反映

## 出力（update plan の役割）
- add: 新規ノード/リレーションの追加
- update: 既存ノードの修正（title, description, tags など）
- supersedes/obsolete: 原則慎重（長期方針を消さない）
  - 短期優先は補助decisionとして追加し、長期decisionは残す（refineの関係で表現）

## 最小運用ルール（opsとの整合）
- commits:
  - 追跡する証跡: approved_plan.json, *bundle*.yaml, docsの確定文書
  - 追跡しない中間生成物: snapshot_raw / seed_plan / suggestion_plan

## 次の成果物（v1のDoD）
- engine_design v1（この文書）が docs に存在
- この文書を入力にした update cycle が走り、canonical に「process/guideline/task」ノードが反映される
