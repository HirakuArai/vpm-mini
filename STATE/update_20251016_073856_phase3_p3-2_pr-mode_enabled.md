# Phase 3 – P3-2 自動PR方式へ移行
- 変更: render_grafana_png.yml を main直コミットから「成果物PR」提出に切替
- ラベル: p3-2 / evidence / bot
- 理由: ブランチ保護の遵守とレビュー導線の確保
- 検証: ワークフローを self-hosted Runner で実行 → PR #389 (bot/p3-2-render/18544296178) が自動生成され、PNG/MD を提出
- メモ: GitHub Actions 由来PRでは必須チェックが自動起動しないため、pr-validate/CI/healthcheck を workflow_dispatch で補完しステータス付与（保護ルール通過には追加調整が必要）
