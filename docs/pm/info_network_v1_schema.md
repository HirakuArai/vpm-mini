# info_network v1 schema（VPMコア用）

## 目的

本ドキュメントは、PM Kai（VPMコア）が扱う情報ネットワークの基本スキーマを定義する。

- プロジェクトごとの reality（現実）を、PM視点で扱いやすい info_node / info_relation に写像する。
- project_id = vpm-mini / hakone-e2 / company-x … など、VPMコアとしての情報だけを対象とする。
- 箱根駅伝そのもののシーンや感情（emotion）は、このスキーマの外側にあるドメイン固有データとして扱う。

## info_node_v1

共通フィールド:

```yaml
info_node_v1:
  id: "hakone-e2:fact:state-current:2025-11-30-01"
  project_id: "hakone-e2"            # vpm-mini / hakone-e2 / company-x ...
  kind: "fact"                       # fact | norm | process | task | decision | metric | guideline | meta
  subkind: "state_snapshot"          # kind ごとの細分類（後述）

  title: "hakone-e2 Phase 1 の現在地サマリ"
  summary: "箱根駅伝の出来事のエモーショナルな扱い方を実験するPoCとして、最初のcurrent_stateが定義された。"
  body: |
    必要なら複数行。STATE/current_state.md の該当箇条書きの、意味としての展開を置く。

  scope:
    project_phase: "phase1"          # phase0/1/2...
    lane: "pm_core"                  # pm_core / doc_update / pm_snapshot / hakone_e2_core など
    file: "STATE/hakone-e2/current_state.md"
    section_anchor: "1.1 Current"    # 見出しや行アンカー

  status: "active"                   # active | draft | obsolete | proposal
  importance: "normal"               # low | normal | high | critical

  created_at: "2025-11-30T12:34:56+09:00"
  updated_at: "2025-11-30T12:34:56+09:00"

  source_refs:
    - kind: "file"
      value: "STATE/hakone-e2/current_state.md"

  authored_by: "kei"                 # kei | kai | aya | system
  review_status: "unreviewed"        # unreviewed | human_ok | ai_ok | deprecated
```

kind（VPMコアで使う種類）:

VPMコアでは、次の kind のみを第一クラスとして扱う。

- fact
  - 事実・状態・構成
  - 例: current_state の C/G/δ、project_definition の目的・制約、infra_snapshot など
- norm
  - ルール・方針・ポリシー
  - 例: SSOT ポリシー、Doc Update の運用ルール
- process
  - フロー・手順・レーンの説明
  - 例: doc_update レーンのステップ、layer_b_update_flow
- task
  - T-*** 系タスク（1タスク = 1ノード）
- decision
  - 方針決定・採否・ピボット
- metric
  - KPI・状態指標
- guideline
  - 設計原則・ベストプラクティス
- meta
  - info_network / view / VPM設計そのものに関するメタ情報

※ hakone-e2 の「scene」や「emotion」は、VPMコアでは扱わない（別レイヤー / 別スキーマで扱う）。

subkind（例）:

kind ごとに、次のような subkind を想定する。

- kind = fact
  - project_meta（目的・背景・スコープ）
  - state_snapshot（current_state の C/G/δ 要約）
  - weekly_summary
  - infra_snapshot
- kind = norm
  - ssot_policy
  - update_policy
- kind = process
  - lane_spec（doc_update レーン、pm_snapshot レーンなど）
  - layer_b_flow
- kind = task
  - pm_task（T-PM-*）
  - infra_task（T-INF-*）
  - doc_task（T-DOC-*）
- kind = decision
  - design_decision
  - scope_decision
- kind = metric
  - cost_metric
  - latency_metric
- kind = guideline
  - pm_guideline
- kind = meta
  - info_model_note
  - view_definition

subkind はプロジェクトの進行に応じて増えてよいが、VPMコアとしては上記をベースラインとする。

## info_relation_v1

共通フィールド:

```yaml
info_relation_v1:
  id: "hakone-e2:rel:2025-11-30-001"
  project_id: "hakone-e2"

  type: "evidence_for"
  # belongs_to | part_of | refers_to | derived_from
  # evidence_for | conflicts_with | supersedes | similar_to

  from: "hakone-e2:task:H2-PDEF-1"
  to:   "hakone-e2:fact:project_meta:2025-11-30-01"

  strength: 0.9                     # 0.0〜1.0（結びつきの強さ）
  status: "active"                  # active | obsolete | tentative

  source_refs:
    - kind: "file"
      value: "STATE/hakone-e2/current_state.md"

  created_at: "2025-11-30T13:00:00+09:00"
  updated_at: "2025-11-30T13:00:00+09:00"
```

relation type（VPMコアで主に使うもの）:

- belongs_to
  - ノードAはノードBの「子」である
  - 例: タスク → プロジェクト、Current要約 → hakone-e2 state_snapshot ルート
- part_of
  - 構造上の部分
  - 例: phase1_snapshot → hakone-e2_snapshot_all
- refers_to
  - A は B を参照している（ゆるいリンク）
- derived_from
  - A は B を要約／変形したもの（pm_snapshot → STATE など）
- evidence_for
  - A は B（fact/norm/decision）の証拠になっている
- conflicts_with
  - A と B は矛盾している可能性がある（Layer B での矛盾検出用）
- supersedes
  - A が B を置き換えた（旧 current_state を新しいものが上書きした場合）
- similar_to
  - 内容が似ている（パターン検出用／必須ではない）

今後、Kai / Aya / Tsugu は、この info_node_v1 / info_relation_v1 を前提に
project_id ごとの「PM視点の意味ネットワーク」を構築する。
