# Phase 0 実行計画（固定版）

本計画は **Claude Code への 1 回指示 = 1 ステップ** として、Phase 0 を完了させるための具体タスクを整理したもの。各ステップには **DoD (完了判定)** を明記。

---

## Step 1 — 5 Roles の最小スケルトン雛形を追加

* **内容**: `src/roles/` に 5 ファイル追加（watcher/curator/planner/synthesizer/archivist）。`run(payload: dict) -> dict` を持ち、プレースホルダ出力を返す。`playground.py` に `run_once(input_text: str)` を実装。
* **DoD**: `python playground.py "hello"` で 5 行の通過ログが表示。

## Step 2 — 共通 JSON スキーマを追加

* **内容**: `schema/v1.json` を追加。I/O 構造を定義し、pydantic で検証。`playground.py` で各ロール実行前後に検証挿入。
* **DoD**: スキーマ不整合で例外→非ゼロ終了。整合なら 0 終了。`make test` green。

## Step 3 — EG-Space(最小) の書き込みを実装

* **内容**: `egspace/store.py` を追加。`append_event(event)` と `register_index(vec_id, raw_ref)` を実装。Watcher と Curator 実行後に書き込む。
* **DoD**: `egspace/events.jsonl` に追記、`index.json` に逆引きリンク。

## Step 4 — Digest/Nav から EG-Space への逆引きリンクを埋める

* **内容**: `digest.run()` / `nav.md` 生成ロジックに `vec_id` 逆引きを追加。
* **DoD**: Digest/Nav に `vec_id` と原文パスが表示。

## Step 5 — 会話 UI / CLI から “ワンコマンド導線” を実装

* **内容**: UI ボタン/CLI サブコマンドから一括で log→summary→digest→nav→egspace を実行。
* **DoD**: 1操作で log/memory.json/digest/nav が更新。

## Step 6 — healthcheck を「5ロール一巡＋JSON妥当＋≤400字」へ拡張

* **内容**: `scripts/healthcheck.sh` と `tests/` を拡張。
* **DoD**: `make test` で green。`quality.json` に summary\_len\_ok: true が残る。

## Step 7 — 観測値 coverage.json / lag.json を出力

* **内容**: `reports/coverage.json` と `reports/lag.json` を run-all 時に生成。CI でアーティファクト保存。
* **DoD**: CI 実行後に両ファイルが artifacts に出力。

## Step 8 — CI ワークフローを Phase 0 判定に合わせて更新

* **内容**: `.github/workflows/ci.yml` を更新。diagram export と reports 保存を追加。Status Check が Auto-merge と連動。
* **DoD**: PR 上で CI green → 自動マージ。Artifacts 確認可。

## Step 9 — ドキュメント更新（README / STATE）

* **内容**: README に "10分再現" 手順を追記。`STATE/current_state.md` を Phase 0 用に更新。
* **DoD**: 新規マシンで README の通りに Phase 0 再現可能。STATE が Phase 0 に更新。

## Step 10 — PR 粒度でコミット分割 & ルール連動確認

* **内容**: 上記 Step を小 PR に分割。各 PR に DoD を記載。Auto-merge 予約。最後に `Phase 0 Complete` Issue を立ててスクショ添付。
* **DoD**: すべての PR が自動マージ、Issue close。main が常時 green。

## ✅ Step 11（実施済み） — δ メトリクス実装

* **内容**: `src/metrics/collector.py` に δ 指標（delta_events, delta_reflect_rate）を実装。coverage.json に出力。ドキュメント／図表を更新。
* **DoD**: coverage.json に δ 指標が出力され、関連ドキュメントが更新済み。

---

# 運用ルール

* Claude Code への依頼は本計画の Step を順番に実行。
* 完了後はチェックマークを付け、進捗を可視化。
