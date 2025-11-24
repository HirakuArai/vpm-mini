# Doc Update Pipeline v1
repo=vpm-mini / branch=main  
Phase 2 (PM Kai v1 + Layer B / Proposer & Reviewer Kai → Codex 連携フェーズ)

このドキュメントは、PM Kai v1 による **ドキュメント更新パイプライン**を定義する。

- Proposer Kai（提案者）
- Reviewer Kai（評価者）
- Human（啓＋ChatGPT）
- Codex（実行器）

の 4 つの役割が、JSON を中心にどのように連携するかを示す。

---

## 1. 目的とスコープ

### 1.1 目的

- Kai がプロジェクトの進捗を読み取り、
  「どのドキュメントを、なぜ、どう更新すべきか」を **JSON 形式**で提案する。
- 別レイヤーの Kai が、その提案を **JSON 形式**で評価する。
- Human（啓＋ChatGPT）は、JSON の中身は書き換えず、
  **採用するかどうか（Accept/Reject）を判断する**ことに集中する。
- 採用された提案 JSON を、Codex が **そのまま読み込んで更新＋PR** まで実行する。

### 1.2 スコープ

このパイプラインが扱う対象は、以下のファイル群：

- docs/projects/<project_id>/project_definition.md
- STATE/<project_id>/current_state.md
- reports/<project_id>/YYYY-MM-DD_weekly.md
- その他、プロジェクトに紐づく Markdown / JSON ドキュメント

---

## 2. 役者と成果物

### 2.1 Proposer Kai（提案者）

ワークフロー:

- .github/workflows/pm_snapshot.yml
  - 出力: pm_snapshot_v1 JSON＋Markdownビュー
- .github/workflows/doc_update_proposal.yml
  - 出力: doc_update_proposal_v1 JSON

成果物:

- pm_snapshot_v1  
  - C / G(short, mid) / δ / Next 3 / Evidence
- doc_update_proposal_v1
  - updates[]（どのファイルを、なぜ、どう変えるか）
  - no_change[]
  - notes[]

### 2.2 Reviewer Kai（評価者）※新設

Proposer Kai の doc_update_proposal_v1 を評価し、
「どの更新提案をどう扱うべきか」を JSON で返す。

成果物:

- doc_update_review_v1 JSON（詳細は doc_update_review_v1_spec.md を参照）
  - proposal 全体の評価（overall_assessment）
  - 各 updates に対する judgement（accept / reject など）
  - 補足メモ（notes）

Reviewer Kai 自身はファイルを直接編集しない。

### 2.3 Human（啓＋ChatGPT）

- Proposer Kai → Reviewer Kai の JSON を読み、
  - 提案内容
  - リスクレベル
  - judgement 内容
- を踏まえて **採用/不採用を決める**。

Human が原則としてやらないこと:

- doc_update_proposal_v1 / doc_update_review_v1 の中身を直接書き換えること  
  （Kai の出力は Kai の「公式アウトプット」として尊重する）

必要に応じて:

- コメントやメモを別ファイル／Issue コメントとして残す。

### 2.4 Codex（実行器）

- Human が「採用」と判断した doc_update_proposal_v1 を受け取り、
- JSON を解析して updates[] の内容を対象ファイルに適用する。
- コミット＋PR作成までを担当する。

Codex は内容を再解釈せず、
**target.path / change_type / suggestion_markdown に従って機械的に適用**する。

---

## 3. パイプラインのフロー

### 3.1 トリガー（進捗の発生）

- 啓が「最近の進捗」を progress_summary としてまとめる。
- 対象の project_id を決める（例: vpm-mini, hakone-e2）。

### 3.2 Proposer Kai フェーズ

1. pm_snapshot.yml を project_id 指定で実行
   - 最新の C / G / δ / Next 3 / Evidence を取得
2. doc_update_proposal.yml を実行
   - 入力:
     - project_id
     - progress_summary
   - 出力:
     - reports/doc_update_proposals/YYYY-MM-DD_<project_id>.json
       （doc_update_proposal_v1）

### 3.3 Reviewer Kai フェーズ

1. Reviewer Kai が doc_update_proposal_v1（＋必要に応じて SSOT）を読む
2. doc_update_review_v1 を出力
   - proposal_ref で proposal JSON を参照
   - overall_assessment に全体評価
   - update_judgements[] に各 updates への judgement
3. doc_update_review_v1 は JSON のみを SSOT とし、
   必要なビューは後から生成する。

### 3.4 Human フェーズ（採用/不採用の判断）

Human（啓＋ChatGPT）は：

1. doc_update_proposal_v1 と doc_update_review_v1 をセットで読む
2. 次を判断する:
   - 今回の proposal を **丸ごと採用してよいか？**
   - or 今回は見送るべきか？
3. 判断結果は、以下のいずれかで記録する（運用レベルで決定）:
   - Issue コメント
   - reports/... 配下のメモファイル
   - あるいは将来の apply_plan JSON（部分適用フェーズ用）

Phase 2 では、まず **proposal 全体の Accept/Reject** から始める。

### 3.5 Codex フェーズ（適用＋PR）

1. Human が **ACCEPT** と判断したら、
2. Codex に対して、統一テンプレートのブリーフを渡す:
   - プロジェクト: HirakuArai/vpm-mini
   - PROPOSAL_PATH=reports/doc_update_proposals/YYYY-MM-DD_<project_id>.json
   - 「この PROPOSAL を読み、updates[] を適用して PR を作成してほしい」

Codex は:

- target.path に対して、change_type / suggestion_markdown で編集
- コミット＋ PR 作成
  - PR タイトルや本文には、PROPOSAL_PATH と主な変更点（updates の要約）を含める。

---

## 4. JSON を SSOT にする方針

- PM Kai の「考えた結果」は、原則すべて JSON を SSOT とする。
  - pm_snapshot_v1 → JSON を「正」とし、Markdown はビュー。
  - doc_update_proposal_v1 → JSON が「正」。
  - doc_update_review_v1 → JSON のみ。
- 人間向けの読みやすさは、
  - JSON → Markdownビュー生成
  - JSON → LLMによる解説テキスト
  で吸収する。

---

## 5. 将来の拡張について（メモ）

- 部分適用（updates 単位の Accept/Reject）を扱いたくなった場合は、
  - apply_plan のような別 JSON を導入し、
  - doc_update_proposal_v1 自体は不変のままにする。
- 自動マージレベルの引き上げ（人間レビューを薄くする）は、
  - doc_update_review_v1.overall_assessment.risk_level
  - 過去の手修正ログ
  を根拠に、後続フェーズで検討する。
