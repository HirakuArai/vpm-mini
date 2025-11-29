# Kai docs index (Kai-0 / vpm-mini)

このディレクトリは Kai（PM アシスタント人格）の仕様や設計メモを集約する場所です。現時点では Kai-0（vpm-mini / Layer B / Doc Update 向けの現場アシスタント）が中心です。

context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Layer B cycle-1 / Kai-0 design)

## Kai-0 関連ドキュメント一覧
- Kai-0 I/O spec v1
  - パス: docs/kai/kai_io_spec_v1.md
  - 内容: kai_request_v1 / kai_response_v1 と、lane_status_v1 / what_changed_v1 の payload 構造を定義。
- Kai-0 JSON examples
  - パス: docs/kai/examples/lane_status_v1_example.json
  - パス: docs/kai/examples/what_changed_v1_example.json
  - 内容: vpm-mini / Layer B / Doc Update の cycle-1 を想定したサンプル JSON。
- Kai-0 usage guide v1
  - パス: docs/kai/kai0_usage_guide_v1.md
  - 内容: Kai-0 に投げる問いと応答の読み方をまとめた人間向けガイド。

## 現時点の Kai-0 スコープ
- 対象 project_id: vpm-mini
- 対象レーン: Layer B / Doc Update
- できること
  - lane_status_v1: レーンの現在地（cycle と Aya/Sho/Tsugu の状態、STATE への反映状況）を返す
  - what_changed_v1: 直近 N 日で vpm-mini に起きた主な変化を返す
- 役割
  - 司令塔ではなく「ChatGPT の現場アシスタント」として設計
  - 黒板や STATE、PR を読み、構造化 JSON と短いサマリを返す

## 関連する外部の場所
- 黒板 Issue
  - Issue 番号: 841
  - 用途: Doc Update レーン用の黒板。Aya / Sho / Tsugu 間のメモやステータスを置く場所。
- ChatGPT / Codex の役割分担メモ
  - ChatGPT: 設計や仕様策定、Kai-0 の振る舞いを対話的に決める
  - Codex: 仕様に基づくファイル追加や PR 作成を実行

## 今後の拡張メモ
- 拡張の方向性
  - Kai-0 をベースに pm_snapshot レーン向けの Kai-1 を設計する可能性
  - persist-report レーン向けの Kai 拡張
  - 他プロジェクト（例: hakone-e2）への水平展開
- 拡張ルール
  - 新しい能力やレーンをカバーするときは、まず I/O spec と JSON サンプルを追加し、その後 usage guide を更新する
  - STATE に Kai の存在を反映する場合は、Layer B / Doc Update レーン（Doc Update Proposal → Review → Apply）を通して更新する
