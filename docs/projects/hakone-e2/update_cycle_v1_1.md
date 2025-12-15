# hakone-e2 update cycle v1.1

## 目的とSSOT
- canonical: `data/hakone-e2/info_nodes_v1.json` / `data/hakone-e2/info_relations_v1.json`
- これらを最新に保つことが目的（Markdownやreports/**は派生物）
- data/** は実験生成物。通常コミットしない

## 入力→出力（処理の連鎖）
0. 新しい情報（memo/weekly/current_state など）
1. bundle 化（info_source_bundle_v1）
2. bundle → snapshot_raw（`tools/info_network/generate_from_bundle_v1.py`）
2-1. 内部矛盾チェック（不明点はオーナーに確認）※TODO
3. seed plan 生成（`tools/info_network/generate_update_plan_v0.py` v0.1 no-op）
4. AI 提案で obsolete/supersedes を補う（`tools/info_network/suggest_update_plan_v1_1.py`）
5. オーナー承認（questions があればここで停止。承認 plan を別名で作る）
6. apply（`tools/info_network/apply_info_update_plan_v1.py`）

## 安全ルール
- questions が 1 件でもあれば自動適用しない（承認 plan を作ってから apply）
- `SUPERCEDES_MIN_CONFIDENCE`（デフォルト 0.85）未満の supersedes は質問に落とす
- confidence は必須。欠落/不正なら再プロンプトし、最後は質問に落として安全側へ
- no-op decision は supersedes 提案対象から除外（v1.1.3）
- supersedes relation は `plan.supersedes` のみから生成（snapshot 由来 supersedes は apply で無視）

## locked/ の扱い（検証再現性）
- `reports/hakone-e2/locked/` は検証用 fixture 置き場
- `EXPECTATIONS.md` に入力ファイルと期待件数を追記して固定
- コミットする fixture の目安: 回帰テストに使うもの（v0.3/v1.0/v1.1 suggestion/approved など）。生成物一式は原則コミットしない
- 上書き禁止: 同名があれば timestamp を付けて新規保存

## 推奨コマンド例
- bundle→snapshot  
  `python tools/info_network/generate_from_bundle_v1.py --bundle <bundle.yaml> --schema-doc docs/pm/info_network_v1_schema.md --model gpt-4.1 --output <snapshot.json>`
- seed plan 生成  
  `python tools/info_network/generate_update_plan_v0.py --canonical-nodes data/hakone-e2/info_nodes_v1.json --canonical-relations data/hakone-e2/info_relations_v1.json --snapshot <snapshot.json> --output <plan_v0.json>`
- v1.1 提案生成  
  `python tools/info_network/suggest_update_plan_v1_1.py --canonical-nodes data/hakone-e2/info_nodes_v1.json --canonical-relations data/hakone-e2/info_relations_v1.json --snapshot <snapshot.json> --model gpt-4.1 --output <plan_suggestion.json>`
- approved plan 作成（questions を空にし notes に承認メモを追記）  
  `python - <<'EOF' ... EOF` などで questions を外して別名で保存
- apply  
  `python tools/info_network/apply_info_update_plan_v1.py --plan <approved_plan.json> --nodes data/hakone-e2/info_nodes_v1.json --relations data/hakone-e2/info_relations_v1.json`

## 既知のTODO
- 2-1 内部矛盾チェックの具体化（矛盾検出/オーナー確認フロー）
- matches（集約/分割）v1.2 の設計
- update cycle の一括実行スクリプト化（chatops/CLI 対応）
