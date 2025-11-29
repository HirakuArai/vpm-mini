# Kai-0 usage guide v1 (vpm-mini / Layer B)

context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Layer B cycle-1 / Kai-0 design)

Kai-0 v1 は vpm-mini 向けの PM アシスタントであり、司令塔ではなく Layer B / Doc Update レーンの現場アシスタントです。ChatGPT や人間からの問いに対して、構造化 JSON と短いサマリを返します。

## 1. 概要
- 対象: vpm-mini の Layer B / Doc Update レーン
- 役割: 現場アシスタントとしてステータスや最近の変化を返す
- 応答形式: 構造化 JSON（payload）と短い Markdown サマリ（summary_md）

## 2. Kai-0 が扱う対象（v1 スコープ）
- project_id: v1 では vpm-mini 固定
- lane: layer=layer_b, name=doc_update
- 提供機能は 2 つ
  - lane_status_v1: Layer B / Doc Update レーンの現在地（例: cycle-1 進捗）
  - what_changed_v1: 直近 N 日で vpm-mini に起きた主な変化

## 3. どういう問いを投げるか（リクエストの考え方）
- 例1: Kai、vpm-mini の Layer B / Doc Update レーンの現在地を lane_status_v1 で教えて。
  - 対応する kai_request_v1.type: lane_status
- 例2: Kai、直近 7 日間で vpm-mini に何が起きたかを what_changed_v1 で要約して。
  - 対応する kai_request_v1.type: what_changed
- 実際の JSON フォーマット（kai_request_v1）は docs/kai/kai_io_spec_v1.md を参照。ここでは「何を知りたいか」を明確にする。

## 4. Kai-0 から返ってくるもの（レスポンスの読み方）
- 応答は kai_response_v1 で表現され、payload.kind に lane_status_v1 または what_changed_v1 が入る。
- payload.data に実データの JSON が格納され、summary_md に人間向けの短い要約が入る。
- 人間は summary_md で全体像を掴み、詳しく知りたいときに payload.data を確認する。
- サンプル: lane_status_v1 は docs/kai/examples/lane_status_v1_example.json、what_changed_v1 は docs/kai/examples/what_changed_v1_example.json。

## 5. サンプルの読み方と活用方法
- lane_status_v1 の読み方
  - cycle.latest_cycle_id と status でサイクルの進捗を確認。
  - steps.aya / steps.sho / steps.tsugu から黒板 entry、artifact、PR の状態を把握。
  - state_view.digest と known_gaps で STATE の認識と未解決課題を確認。
- what_changed_v1 の読み方
  - time_window で対象期間を確認。
  - highlights の rank と summary で重要度の高い出来事を把握。
  - by_category.workflows / prs / state_docs で関係する workflow、PR、STATE 変更を追う。
  - risks と open_questions で認識されているリスクや論点を確認。

## 6. 今後の拡張（簡単なメモ）
- v1 制約: project_id は vpm-mini、lane は Layer B / Doc Update のみ。
- 拡張の方向性
  - pm_snapshot レーンへの拡張
  - persist-report レーンへの拡張
  - 他プロジェクト（例: hakone-e2）への水平展開
- 拡張時は docs/kai/kai_io_spec_v1.md と JSON サンプルを先に更新し、その後この usage guide も反映する。
