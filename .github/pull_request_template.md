## 目的 (Purpose)
- Why:
- What:

## 変更点 (Changes)
- [ ]
- [ ]

## 動作確認 (How to verify)
- [ ] `make healthcheck` → ✅ Green（Run URL: ）
- [ ] `pytest -q` → ✅ Green
- [ ] `python cli.py <obj> "テスト"` 実行後に `objectives/<obj>/logs/*.jsonl` が追記される
- [ ] `objectives/<obj>/memory.json` 先頭に要約（≤400字）が追加される

## Evidence（証拠）
- CI Run URL:
- Artifacts (reports/*.json):
- スクリーンショット:

## 影響範囲 (Impact)
- [ ] CLI / Streamlit UI
- [ ] src/core/logging.py
- [ ] src/core/summary.py
- [ ] schema/*.json
- [ ] STATE/current_state.md

## リスク・確認事項 (Risks)
- [ ] スキーマ互換（summary.v1.json / memory.v1.json）
- [ ] 冪等性（重複抑止）
- [ ] 秘密情報なし

## 関連 Issue
Fixes #

## 完了条件（DoD）
- [DoDリンク](https://github.com/users/HirakuArai/projects/1?pane=issue&itemId=123637605)

## チェックリスト (Reviewer ready)
- [ ] 説明が埋まっている
- [ ] テストを追加／更新した
- [ ] STATE/current_state.md を更新した
