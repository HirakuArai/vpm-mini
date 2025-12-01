# Kai-assist I/O spec v1 (vpm-mini)

context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Kai-0 / Kai-assist v1)

このドキュメントは、Kai-0 がレーンの現在地レポート以外のアシスタント業務（プロンプト調査、Workflow レビューなど）を扱うための共通 I/O 仕様を定義する。kai_task_request_v1 / kai_task_response_v1 を定め、最初の task_type として inspect_pm_snapshot_prompt_v1 を登録する。

## 1. Kai-assist の位置づけとスコープ v1
- Kai-0 のアシスタント業務用レーン。例: Workflow やプロンプトを読み、問題箇所と修正文案を出す、特定ファイルの構造を要約する。
- v1 スコープ: project_id は vpm-mini に限定し、task_type は inspect_pm_snapshot_prompt_v1 の 1 種類から開始。
- lane_status_v1 との関係: lane_status_v1 はレーンの現在地レポート専用。Kai-assist は設定やプロンプトのレビュー・提案を扱う別レーン。

## 2. 入力: kai_task_request_v1
- 目的: Kai-assist に「何をしてほしいか」を渡す共通フォーマット。
- フィールド案:
  - version: "kai_task_request_v1"
  - request_id: 一意な文字列（タイムスタンプなど）
  - project_id: 例 "vpm-mini"
  - task_type: 例 "inspect_pm_snapshot_prompt_v1"
  - params: タスク固有パラメータ（オブジェクト）
- JSON イメージ（文章表現）:
  - version: "kai_task_request_v1"
  - request_id: "2025-11-30T23:59:00+09:00_inspect_pm_snapshot_prompt"
  - project_id: "vpm-mini"
  - task_type: "inspect_pm_snapshot_prompt_v1"
  - params:
    - target_workflow: "pm_snapshot"
    - include_files: [".github/workflows/pm_snapshot.yml"]
    - notes: "pm_snapshot が STATE/weekly を直接更新するような表現がないか確認し、修正文案を出してほしい"

## 3. 出力: kai_task_response_v1
- 目的: Kai-assist がタスク結果を返す共通フォーマット。
- フィールド案:
  - version: "kai_task_response_v1"
  - request_id: 対応する kai_task_request_v1 の request_id
  - status: "ok" または "error"
  - task_type: 例 "inspect_pm_snapshot_prompt_v1"
  - payload: タスク固有の JSON（次章）
  - summary_md: 人間向け短い Markdown サマリ（数行）
  - notes: 任意の補足メモ配列
- JSON イメージ（文章表現）:
  - version: "kai_task_response_v1"
  - request_id: "2025-11-30T23:59:00+09:00_inspect_pm_snapshot_prompt"
  - status: "ok"
  - task_type: "inspect_pm_snapshot_prompt_v1"
  - payload: { … }
  - summary_md: "pm_snapshot プロンプト内のレイヤーBサイクル表現を確認し、2箇所を修正候補として提案しました。"
  - notes: [".github/workflows/pm_snapshot.yml の system メッセージにショートカット表現がありました。", "修正文では『pm_snapshot → 現実のアクション → Aya/Sho/doc_update → PR → STATE追随』という流れに統一しています。"]

## 4. task_type: inspect_pm_snapshot_prompt_v1
- 目的: PM Snapshot (vpm-mini) のプロンプトや説明文を読み、pm_snapshot の責務が C/G/δ/Next の整理に限定されているか、STATE/weekly 更新まで自分の仕事と誤解されていないかをチェックし、問題箇所と修正文案を返す。
- 入力 params 想定:
  - target_workflow: "pm_snapshot"
  - include_files: [".github/workflows/pm_snapshot.yml"] ほか、必要なら pm_snapshot 用プロンプトを含むファイル
  - notes（任意）: 追加コメント
- 出力 payload 構造案:
  - kind: "inspect_pm_snapshot_prompt_v1"
  - project_id: "vpm-mini"
  - target_workflow: "pm_snapshot"
  - findings: 配列
    - location: ファイルパス＋行の識別（例: ".github/workflows/pm_snapshot.yml: system_prompt 段落 3 行目"）
    - snippet: 問題になり得る文言の抜粋
    - issue: 何が問題かの説明
    - suggestion: 修正文案
  - recommendations: 実装側でやるべき変更まとめ（箇条書き）
- payload イメージ（文章箇条書き）:
  - kind: "inspect_pm_snapshot_prompt_v1"
  - project_id: "vpm-mini"
  - target_workflow: "pm_snapshot"
  - findings:
    - location: ".github/workflows/pm_snapshot.yml: system_prompt 段落 3 行目"
    - snippet: "レイヤーB最小サイクル（pm_snapshot → STATE/weekly 更新案 → PR → マージ）"
    - issue: "pm_snapshot が STATE/weekly を直接更新するかのようなショートカット表現になっている。現実のアクションや Aya/Sho/doc_update の責務が抜けている。"
    - suggestion: "レイヤーB最小サイクルは『pm_snapshot → そこで整理された Next 候補をもとに現実のアクションを選ぶ → Aya/Sho/doc_update が STATE/weekly を追随させる』という流れで表現する。"
  - recommendations:
    - ".github/workflows/pm_snapshot.yml の system プロンプト内で、pm_snapshot の責務を「C/G/δ/Next を整理すること」に限定する一文を追加する。"
    - "レイヤーBサイクルの説明文は、『pm_snapshot → 現実のアクション → Aya/Sho/doc_update → PR → STATE追随』という形に書き換える。"

## 5. task_type: inspect_doc_update_proposal_flow_v1
- 目的: Doc Update Proposal (Aya) workflow と黒板読み取りロジックを調査し、黒板 Issue #841 のどのエントリをどう選び、どのフィールドをプロンプトに使っているかを確認する。payload_ref / target_docs / change_intent を見落としていないか、今回のような manual_note リクエストが拾われなかった理由と修正案を findings / recommendations で返す。
- 入力 params 想定:
  - target_workflow: "doc_update_proposal_pm"
  - include_files:
    - ".github/workflows/doc_update_proposal.yml"
    - Aya が黒板を読むスクリプト（存在する場合）
  - blackboard_issue: 841
  - notes（任意）: 人間から Kai への追加コメント
- 出力 payload 構造案:
  - kind: "inspect_doc_update_proposal_flow_v1"
  - project_id: "vpm-mini"
  - target_workflow: "doc_update_proposal_pm"
  - findings: 配列（location, snippet, issue, suggestion を含む）
  - recommendations: 配列（黒板選択ロジックの修正案、処理した entry の source_id を proposal/review JSON に記録する案など）
- summary_md: 調査結果の要点を数行で Markdown 要約。

## 6. task_type: inspect_ci_for_tsugu_pr_v1
- 目的: .github/workflows 下の CI ワークフロー（evidence-dod / healthcheck / k8s-validate / knative-ready / test-and-artifacts など）を読み、Tsugu PR（author=github-actions, head_ref=feature/doc-update-apply-*）で Required checks が走らない理由と、どう条件を変えれば動くかを findings / recommendations として返す。
- 入力 params 想定:
  - target_checks: ["evidence-dod", "healthcheck", "k8s-validate", "knative-ready", "test-and-artifacts"]
  - include_files: ".github/workflows/*.yml", ".github/workflows/*.yaml"
  - notes（任意）: Tsugu PR の head_ref パターンなど補足コメント
- 出力 payload 構造案:
  - kind: "inspect_ci_for_tsugu_pr_v1"
  - project_id: "vpm-mini"
  - target_checks: 上記チェック名配列
  - findings: 配列（check_name, workflows, location, snippet, issue, suggestion）
  - recommendations: 配列（if 条件や paths の修正案、branch protection 設定の見直しなど）
- summary_md: 調査結果の短い Markdown サマリ（数行）

## 7. 将来の task_type 拡張メモ
- inspect_workflow_v1: 任意の Workflow の役割とリスクを要約。
- propose_state_patch_v1: ある snapshot を前提に、STATE の特定セクション更新案を JSON パッチで提案。
- これらも kai_task_request_v1 / kai_task_response_v1 を共通で使い、task_type と payload の中身だけ変える方針。
