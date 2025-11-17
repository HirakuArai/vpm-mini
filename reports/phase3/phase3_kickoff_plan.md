# Phase 3 Kickoff Plan (Draft)

context_header: repo=vpm-mini / branch=main / phase=Phase 3

本レポートは、Phase 2 / M2 Exit スナップショットと各種メモ（STATE, phase3_skeleton, metrics_echo_design など）を前提に、Phase 3 で何をどの順番で進めるかを整理したキックオフプランのドラフトである。

参照ドキュメント:

- STATE/current_state.md
  - Phase 2 / M2 snapshot
  - Phase 3 (draft)
- docs/overview/phase3_skeleton.md
  - Phase 3 の仮テーマ, マイルストーン, Execution Policy, セル候補一覧
- docs/memory/egspace_m2_insights.md
- docs/memory/metrics_echo_design.md
- docs/memory/u_contract_policy.md
- reports/phase2/phase2_m2_exit_summary.md

---

## 1. Phase 3 の目的（再確認）

Phase 3 の仮テーマ（要約）:

- 少数セルで成立した「/ask + Codex + 人間 + u_contract」による自己更新ループを、**小規模 Swarm（〜30 セル）** に拡張する。
- EG-Space 上で、どのセルがどのレーンに属し、C/G/δ がどうなっているかを「地図」として見えるようにする。
- ソース改修やインフラ操作の実行主体を、ローカル Mac Codex からエージェントレーン（LLMリレー / VM Codex）へシフトする準備を進める。

キーワード:

- 小規模 Swarm（~30 cells）
- /ask + u_contract + Evidence の常時サイクル
- EG-Space の可視化
- 実行主体のエージェント化（Execution Policy）

---

## 2. Phase 3 のマイルストーン案

### P3-1: Skeleton & Cell Map

目的:

- Phase 3 で扱うセル候補を整理し、「どのセルをどのレーンとして扱うか」の地図を作る。
- hello-s5 / metrics-echo / persist-report レーン / self-cost など、基礎セル群の役割と関係性を明確にする。

具体的なアウトプット案:

- docs/overview/phase3_skeleton.md の「Phase 3 セル候補一覧（Draft）」を更新し、
  - Cell key
  - 役割（レポート / 監視 / コスト / North Star など）
  - u_contract カテゴリ（案）
  - /ask 対応有無（案）
- 必要であれば、セル間の関係を簡単な図（別ファイル）として整理。

### P3-2: Multi-cell /ask & u_contract Loop

目的:

- Hello S5 以外に **2〜3 個のセル**で、
  - Evidence（レポート or メトリクス）
  - /ask 実行
  - patch 生成
  - 人間判断＋PR
  - STATE / memory / EG-Space への反映
  のループを回す。

具体的なターゲット候補:

- persist-report レーンの一部セル
- （可能であれば）metrics-echo などの監視系セル（まずは READY / 成功率だけ）

成功条件のイメージ:

- 日次〜数日単位で、複数セルについて Evidence → Decision → Action が途切れず回っていること。
- /ask の CONTEXT / u_contract のポリシー / STATE 更新のパターンが複数セルで共通化されていること。

### P3-3: Self-Cost / 基盤ヘルス系セルの追加

目的:

- Runner 利用状況 / クラスタコスト / Self-Cost を扱うセルを追加し、「自分自身の土台の状態」を監視する Swarm の最小セットを作る。

具体的な検討項目:

- self-cost セルの North Star（案）
- どのメトリクスを Evidence として扱うか
- /ask および u_contract の適用タイミング

---

## 3. Phase 3 で扱うセル候補（再掲＋補足）

docs/overview/phase3_skeleton.md の「Phase 3 セル候補一覧（Draft）」を前提に、代表的なセル候補と Phase 3 での使い方イメージをまとめる。

### hello-s5

- 種別: North Star デモ / 模範セル
- 役割: /ask update_north_star → patch → PR → STATE/メモリ/EG-Space 同期 の模範ケース
- Phase 3 での扱い:
  - 「正しいループがどういうものか」を示すリファレンスとして維持。
  - 他セルの設計時に、Hello S5 のパターンをテンプレートとして用いる。

### metrics-echo

- 種別: 監視 / SLI セル候補
- 役割: READY / 成功率など、サービスのヘルスに関する North Star を扱う。
- Phase 3 での扱い:
  - `docs/memory/metrics_echo_design.md` に沿って、
    - READY / 成功率 SLI 向け Evidence ラインを整備。
    - CONTEXT_JSON に `kservice_status` / `sli_summary` を含めた形で /ask を再実行。
  - Phase 3 前半では「最低限の SLI」で留め、詳細なレイテンシやコストは Phase 4 以降の宿題とする。

### persist-report レーン（reports/**）

- 種別: レポート系セル群
- 役割: `persist-report` カテゴリの PR に対し、半自動の整理＋1クリックマージを行うレーン。
- Phase 3 での扱い:
  - Phase 2 / M2 で確認した「半自動レーン」を維持しつつ、
    - /ask でレポート内容のサマリやタグ付けを行うセルの可能性も検討。

### self-cost

- 種別: コスト / 基盤ヘルス系セル候補
- 役割: Runner 利用状況やクラスタコストを監視し、Self-Cost に関する North Star を扱う。
- Phase 3 での扱い:
  - Phase 3 後半〜4 にまたがる可能性が高いセルとして、設計のみ先に進める。
  - 具体的な Evidence や SLI は今後の検討とする。

### その他候補

- Biz KPI セル
- 追加の North Star セル
- サンプル系（sample-candidate / sample-archive）セル

---

## 4. Execution Policy と実行レーンの整理

Phase 3 では、Phase 2 / M2 で定義した Execution Policy を実際の運用に落としていく。

ポイント:

- 標準ルート:
  - ChatGPT / Planner が仕様（What/Why）を文章で整理。
  - Codex / LLMリレー / VM Codex へ「実行指示書」として渡す。
  - エージェントが実行し、PR として反映。
  - 人間（啓さん）は意味・整合性・リスクのレビューに集中。
- 例外ルート:
  - SLO を脅かす緊急障害時のみ、人間が直接編集。
  - その場合も理由と diff を後追いで記録（STATE / reports / PR コメントなど）。
- 権限境界:
  - Phase 3 のどこかのタイミングで、「書き込み可能な実行レーン」を VM Codex 等に限定していく。

Phase 3 Kickoff では、この Execution Policy を前提として、「どのタスクをどのレーン（ローカル Mac Codex / VM Codex / hosted runner 等）に割り当てるか」を段階的に決めていく。

---

## 5. リスクとオープンクエスチョン

想定されるリスク:

- セル数増加に伴い、Evidence / /ask / u_contract / STATE 更新の整合性が崩れる可能性。
- 実行レーンの分散（ローカル VS VM VS hosted）による混乱。
- metrics-echo や self-cost など、「監視系セル」の North Star の粒度を決めきれないまま走り始めてしまうリスク。

オープンクエスチョン（例）:

- 30 セル前後をどのくらいのタイムスパンで目指すか？
- Phase 3 の中で、どこまでを「日常運用で使えるライン」とみなすか？
- VM Codex / LLMリレー 環境をどのタイミングで常設化するか？

これらは Phase 3 Kickoff ミーティングや次セッションで逐次詰めていく前提とする。

---

## 6. 次の具体アクション候補

Phase 3 Kickoff に向けて、直近で取りやすいアクション例:

1. hello-s5 / metrics-echo / persist-report レーン / self-costについて、
   「どのマイルストーンで何をするか」を簡単な表にして skeleton に反映する。
2. metrics-echo について、READY / 成功率 Evidence の最小ライン（人手 + 既存メトリクス）から試しに 1 回 /ask を再実行してみる。
3. Execution Policy を前提に、Codex / VM ごとの「役割分担メモ」を短く作る。


---

## 7. Phase 3 next focus after P3-2 (Draft)

- metrics-echo / P3-2 (Round 1) の扱い:
  - READY Evidence (#778) と簡易 SLI Evidence (#783, SUCCESS_RATE=0%) を揃えたうえで、
    `/ask update_north_star` の再実行は plan-only（state_patch / memory_patch なし）となった。
  - READY と devbox からの到達性が食い違っている「要追加 Evidence の監視セル」として、
    Phase 3 P3-2 時点では North Star を固定せず棚上げする。
- 次の実験フォーカス候補（P3-3〜）:
  - persist-report レーン:
    - Phase 2 / M2 で確立した「reports/** 限定 + CI Green → Codex 整理 + 1クリックマージ」の半自動レーンを、
      Phase 3 では /ask + u_contract を組み合わせたセルとして拡張していく候補とする。
    - 具体的には、reports/** の Evidence PR に対して:
      - /ask による要約やラベリング
      - u_contract `persist-report` ポリシーの見直し・拡張
      - stale / archive 対応ルールの整理
      などを小さな実験セルとして増やしていく。
- このセッション終了時点の「次の一歩」イメージ:
  - metrics-echo は P3-2 Round 1 の結果を設計メモ / STATE に刻印したうえで一旦棚上げ。
  - 次の Phase 3 セッションでは、persist-report レーンを P3-3 の主対象候補として扱い、
    どの Evidence PR から /ask + u_contract の実験を始めるかを検討する。
