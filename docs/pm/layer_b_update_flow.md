# Layer B 更新フロー設計: STATE / weekly / pm_snapshot

## 1. 目的

本ドキュメントは、vpm-mini における **レイヤーB（記録・構造化ループ）** の最小更新フローを定義する。

目標は、実行力は人間や外部システムに任せたまま、

- 実行提案（Next 3）
- （人間による）実行
- 実行結果に基づく **STATE / weekly / pm_snapshot の更新案**
- それに基づく次の実行提案

という循環を PM Kai が自分で回せる状態に近づけること。

## 2. 対象と前提

対象プロジェクト: vpm-mini（project_id = "vpm-mini"）

前提として、以下が整備済みである。

- プロジェクト定義  
  - `docs/projects/vpm-mini/project_definition.md`
- 現在地（C/G/δ, Active Tasks）  
  - `STATE/vpm-mini/current_state.md`（2025-11-23 ベースライン）
- 週次レポート  
  - `reports/vpm-mini/2025-11-23_weekly.md` 以降
- PM Snapshot 仕様と標準質問  
  - `docs/pm/pm_snapshot_v1_spec.md`（pm_snapshot_v1 JSON + Markdown / Standard Prompt）
- PM Snapshot 用ワークフロー  
  - `.github/workflows/pm_snapshot.yml`  
    - `workflow_dispatch` により `project_id=vpm-mini` で手動実行可能  
    - OpenAI を呼び出して `pm_snapshot_v1` を生成し、Markdown を artifact として保存
- ドキュメント更新パイプラインとレビュー
  - `docs/pm/doc_update_pipeline_v1.md`
  - `docs/pm/doc_update_review_v1_spec.md`
- Codex 適用ブリーフ
  - `docs/ops/codex_brief_apply_doc_update_v1.md`

本ドキュメントでは、これらを前提に **STATE / weekly 更新案を Kai に生成させるフロー** を設計する。

## 3. 全体フローのイメージ

レイヤーBの最小フローは、以下のステップで構成する。

1. **実行 / 決定が発生**
   - 例: 標準質問の定義 (#809)、STATE ベースライン更新 (#811)、インフラ縮退完了、など。

2. **PM Snapshot の取得（pm_snapshot.yml）**
   - Actions から `pm_snapshot (project_id=vpm-mini)` を実行し、最新の pm_snapshot_v1（JSON + Markdown）を生成する。
   - Artifact として `reports/pm_snapshots/YYYY-MM-DD_vpm-mini.md` が保存される。

3. **STATE / weekly 更新案の生成（Kai）**
   - pm_snapshot_v1 の内容（C/G/δ, Next 3, Evidence, Notes）を入力として、
     - `STATE/vpm-mini/current_state.md` の C/G/δ / Active Tasks に対する **更新案テキスト**
     - `reports/vpm-mini/..._weekly.md` の Done / C/G/δ / Next3 に対する **追記・修正案**
   を、PM Kai に生成させる。

4. **更新案を PR として提示**
   - Kai が生成した更新案をもとに、
     - `STATE/vpm-mini/current_state.md` を編集する PR
     - 必要なら該当週の `reports/vpm-mini/..._weekly.md` を編集する PR
   を作成する（最初は手動／Codex 経由でよい）。

5. **人間によるレビューとマージ**
   - 啓が PR の内容を確認し、「妥当」と感じる部分はそのままマージし、「違和感」のある部分は手で修正したうえでマージする。
   - これにより、「実行結果」が SSOT（STATE / weekly / pm_snapshot）の形で蓄積される。

6. **次の PM Snapshot で変化を確認**
   - 再度 pm_snapshot を実行し、新しい C/G/δ / Next 3 がどう変化したかを見る。
   - これを通じて、「提案 → 実行 → 記録 → 更新された提案」のループが回っているかを確認する。

### 補足（v1 運用）

- Kai が出す更新案は、doc_update_proposal_v1（JSON）として起票する。
- 出力ファイル配置: Kai が生成した提案は `reports/doc_update_proposals/YYYY-MM-DD_<project_id>.json` として保存し、Sho v1 のレビュー入力とする。
- レビューは `docs/pm/doc_update_review_v1_spec.md` に従って行い、必要に応じて修正のうえ PR を作成・マージする。
- Codex を使って適用する場合は、`docs/ops/codex_brief_apply_doc_update_v1.md` のブリーフに従う。

## 4. Kai にやらせたい具体タスク（初期バージョン）

### 4.1 STATE 更新案（current_state）

入力:

- `STATE/vpm-mini/current_state.md` の現行バージョン
- 最新の pm_snapshot_v1（JSON / Markdown）

Kai に求めるアウトプット（テキスト）:

- C（Current）について:
  - 今回の実行・決定を反映して、「現状」を 2〜4 行でどう書き換えるべきか。
- G（Goals）について:
  - 短期／中期ゴールのうち、変える必要がある部分があればその差分。
- δ（Gap）について:
  - 既に解消されたギャップをどう削る／弱めるべきか。
  - 新しく顕在化したギャップがあればそれを追加。
- Active Tasks について:
  - 完了したタスク（例: T-PM-1）のチェック状態やメモをどう更新するか。
  - 新しくフォーカスすべきタスクがあれば、それを追加する形で提案。

最初の段階では、「STATE の全文」ではなく「どこをどう変えるべきかの差分案」をテキストで出してもらい、
人間＋Codex でその差分を反映する。

### 4.2 weekly 更新案（reports）

入力:

- 対象週の `reports/vpm-mini/YYYY-MM-DD_weekly.md`
- 最新の pm_snapshot_v1 と実行内容

Kai に求めるアウトプット（テキスト）:

- 今週やったこと（Done）に追加すべき項目
- 今週のサマリーに足したほうがよい一言
- C/G/δ セクションをどう更新するか（必要なら）
- Next 3 をどう更新／差し替えするか

こちらも同様に、全文ではなく「追記・修正案」として出してもらう。

## 5. 今後の発展（ワークフロー化の方向性）

将来的には、以下のようなワークフローを想定する。

- `pm_snapshot.yml` 実行後に、
  - 最新の pm_snapshot artifact を取得し、
  - Kai に対して「STATE/weekly 更新案」を生成させ、
  - 専用ブランチで `STATE/current_state.md` と weekly を編集した PR を自動作成する。

ただし、レイヤーBの初期段階では、

- Kai の更新案はテキストとして提示するにとどめる
- PR 作成は人間＋Codex で行う
- マージは常に人間が判断する

というセミ自動の形から始める。

## 6. 現時点のステータス（2025-11-30）

- PM Snapshot 仕様（pm_snapshot_v1）と標準質問は `docs/pm/pm_snapshot_v1_spec.md` に定義済み（PR #804, #809）。
- vpm-mini の current_state ベースラインは `STATE/vpm-mini/current_state.md` に反映済み（PR #811）。
- `pm_snapshot.yml` ワークフローから、vpm-mini に対する PM Snapshot を手動で生成可能（PR #805, #806, #807）。
- 5セル観点の `roles_v1` と Aya↔Sho の `blackboard` ドラフトを追加（PR #820, #821）。
- Sho v1 の Doc Update Review Debug ワークフローを整備し、`doc_update_review_v1.json` を生成でき
