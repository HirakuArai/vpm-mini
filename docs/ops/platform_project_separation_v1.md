# Platform / Project 分離ルール v1（vpm-mini）

## 目的
vpm-mini（仕組み）に、特定プロジェクト（例: hakone-e2）の仕様が混入して専用化する事故を防ぐ。

## 原則
- **Project固有の仕様・データ**は `docs/projects/<project_id>/` と `data/<project_id>/` に閉じる
- 仕組み（tools/scripts/workflows）は **project_id を引数に取る汎用**にする
- `tools/**` にプロジェクト名（hakone-e2 等）をハードコードしない

## 例外（許容）
- `.gitignore` に “特定projectの巨大生成物を無視する” ルールを追加するのは可
  - ただし可能なら `reports/**/runs/**` のように一般化する

## 変更レビューの観点
- PRで `tools/**` が変わったら、project_id で汎用に動くかを必ず確認する
- `rg "<project_id>" tools` でハードコードが無いことをチェックする

