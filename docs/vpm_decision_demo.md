# VPM Decision Demo Runbook（5分台本）

## 構成
- `apps/vpm_decision_demo_app.py`: Streamlit 最小UI
- SSOT: `STATE/current_state.md` / `reports/`
- 出力: `out/next_actions.json` / `out/pr_draft.md`

## 台本
1. STATE を投影し、C/G/δ を読み上げる。
2. サイドバーで SSOT を確認しつつ、固定 5 問へ即答する。
3. `next_actions.json` を表示し、優先順位と DoD / リスクを説明。
4. アクションを 1 つ選び、PR 草案の Markdown を提示する。
5. Evidence の保存先 (`reports/` / `reports/img/`) と DoD を再確認。

## 代替手順 / トラブル時
- STATE が欠損: UI が `DEMO_SSOT/` のフェイルオーバを案内。そこで進行。
- UI が起動しない: 事前録画またはスクリーンショットで説明に切り替え。
- 出力が生成されない: `out/` ディレクトリの権限と存在を確認し、再実行。
