# hakone-e2: データファイル運用ルール（H2-OPS-1）v1

## 目的
更新エンジン（既存＋新規）を回すために、保存場所・命名・レビュー・版管理の迷子を防ぐ。

## SSOT（canonical）
- canonical は `data/hakone-e2/` を正とする
  - `data/hakone-e2/info_nodes_v1.json`
  - `data/hakone-e2/info_relations_v1.json`

## run artifacts（実行生成物）
- 実行ごとに `reports/hakone-e2/runs/<timestamp>/` を作る
- 原則コミット対象（証跡として軽いもの）:
  - `approved_plan.json`（意思決定の証跡）
  - `*bundle*.yaml`（入力の証跡）
- 原則コミットしない（肥大化・再生成可能）:
  - `snapshot_raw.json` / `seed_plan_*.json` / その他大きい中間生成物
  - 必要な場合のみ「fixture」として最小限を locked/ に保存する

## bundle（入力）命名規則
- `source_type` / `source_id` / `date` を含める
- bundle は run dir 配下に置く（入力と出力を同じ箱にまとめる）

## 反映フロー（停止条件つき）
1. bundle作成
2. update cycle 実行（bundle→suggestion）
3. `questions > 0` なら停止して人間が回答（approve/applyしない）
4. `questions == 0` なら approve→apply
5. `git diff` で差分確認 → PR化して main に反映

