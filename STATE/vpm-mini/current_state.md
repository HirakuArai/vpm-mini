# STATE: vpm-mini / current_state

最終更新: 2025-11-30 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- フェーズ: Phase 2。インフラ（VM/GKE）を一旦縮退し、「GitHub + LLM の PM Kai v1」にフォーカスしている。
- プロジェクトの SSOT は `docs/projects/vpm-mini/project_definition.md` に定義済み（PR #800）。`STATE/vpm-mini/current_state.md` と `reports/vpm-mini/2025-11-23_weekly.md`, `reports/vpm-mini/2025-11-30_weekly.md` に C/G/δ と進捗を記録（PR #801, #802, #803, #810 ほか）。
- `docs/pm/pm_snapshot_v1_spec.md` に pm_snapshot_v1 の仕様と標準質問を定義し、`.github/workflows/pm_snapshot.yml` から手動実行で Snapshot を生成可能（PR #804, #805, #806, #807, #809）。
- レイヤーB最小更新フロー v1 を `docs/pm/layer_b_update_flow.md` に定義。`docs/pm/doc_update_pipeline_v1.md` と `docs/pm/doc_update_review_v1_spec.md` を追加し、doc_update_proposal_v1 の提案〜レビューの枠組みを整備（PR #817, #818）。
- 5セル観点の整理として `docs/pm/roles_v1.md` を追加し、Kai / Aya / Sho などのロールと5セル構成を定義（PR #820）。また、`docs/pm/blackboard_v1_draft.md` を追加し、Aya↔Sho の伝言形式（「駅の黒板」プロトコル）を整理（PR #821）。
- Sho v1 の Doc Update Review Debug ワークフローを整備し、`doc_update_review_v1.json` を Python で生成できる体制を構築（PR #822〜#835）。vpm-mini で Aya→Sho→Human→反映 の最小サイクルを次週以降に実運用予定。

### 1.2 Goals（G: ゴール）

**短期（〜数週間）**

- PM Kai v1 が、GitHub 上の情報（project_definition / STATE / reports / Issue / PR）だけを読んで、**いつでも vpm-mini の C/G/δ と Next 3 を一貫した形で答えられる状態**にする。
- vpm-mini 用 PM Kai v1 を、他プロジェクトにも展開可能な PM エンジンとして使えるよう、`project_id` 前提の構造と pm_snapshot_v1 仕様を安定させる。
- レイヤーB（記録・構造化ループ）の 1 サイクルを、vpm-mini で実際に回し、「このパターンなら続けられそう」と判断できるレベルまで持っていく。

**中期（〜数ヶ月）**

- 箱根E² や会社業務プロジェクトにも、`docs/projects/<project_id>/project_definition.md`・`STATE/<project_id>/current_state.md`・`reports/<project_id>/..._weekly.md` を整備し、**「マルチプロジェクト VPM」として PM を立てられる状態**にする。
- EG-Space と 5セルを「論理的な視点／座標」として PM Kai に組み込み、物理インフラに依存せずに C/G/δ・Next3 の精度を高める検証を進める。
- レイヤーB（記録・構造化）の最小ループ（PM Snapshot → STATE/weekly 更新案 → PR → マージ）を vpm-mini で安定運用し、必要に応じて他プロジェクトにも展開できる設計にする。

### 1.3 Gap（δ）

- pm_snapshot_v1 の仕様とレイヤーB最小更新フロー v1 は定義済みだが、vpm-mini での実サイクル運用（doc_update_proposal_v1 → STATE/weekly 反映 → 次の Snapshot）の実践が未了。
- 運用ルールの軽量版は本 STATE にドラフトとして追記済み。`docs/pm/doc_update_review_v1_spec.md` との参照関係や例外時の扱いなど、実運用を通じたチューニングが必要。
- Sho v1 Debug ワークフローにより `doc_update_review_v1.json` 生成の検証環境は整ったが、vpm-mini 向けの定常運用（Actions からの起動、アサイン、レビュー動線）に組み込む段取りが未整備。
- PR 自動化（pm_snapshot 実行直後に更新案ブランチを作成する最小フロー）の設計と検証が未完。
- マルチプロジェクト展開に向けた他プロジェクトの project_definition / STATE / reports 整備は未着手（hakone-e2 は試行のみ）。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [x] **T-PM-1:** PM Kai v1 の標準質問と出力フォーマット（pm_snapshot_v1 + Markdown）を定義し、spec に追記する（PR #809 完了）。
- [ ] **T-STATE-1:** この current_state を 2025-11-23 ベースラインとして確定し、C/G/δ と Active Tasks を「数週間はそのまま使える」レベルまで整える（layer_b_update_flow への参照を追記）。
- [ ] **T-PM-2:** `/ask` + GitHub Actions による STATE / weekly 更新ループの設計を進める（pm_snapshot の結果から STATE/weekly 更新案を生成する最小フロー案）（owner: 啓、期限: 2025-12-07 目安）。
- [ ] **T-PM-3:** 他プロジェクト（例: 箱根E² or 会社業務）について、最初の `project_definition` / `STATE` / `weekly` を用意し、pm_snapshot を回してみる（hakone-e2 で doc_update_proposal_v1 → STATE/weekly の1サイクル試行済み）（owner: 啓、期限: 2025-12-14 目安）。
- [ ] **T-PM-4:** vpm-mini で Kai による「STATE/weekly 更新案（テキスト）」生成 → 手動PR の最小サイクルを1回実施して検証する（owner: 啓、期限: 2025-12-07 目安）。
- [ ] **T-INF-1:** VM/GKE 縮退後の GCP インベントリを月次レベルで確認する軽い仕組み（レポート or 手動チェック）を検討する（優先度はレイヤーBより低い）。
- [ ] **T-DOC-1:** doc_update_proposal_v1 を vpm-mini に適用し、STATE/weekly 更新案 → 手動PR → マージの1サイクルを実施する（docs/pm/doc_update_pipeline_v1.md・docs/pm/doc_update_review_v1_spec.md に準拠。適用には `docs/ops/codex_brief_apply_doc_update_v1.md` を使用）（優先度: 高、owner: 啓、期限: 2025-12-07 目安）。
- [ ] **T-AUTO-1:** pm_snapshot 実行後に更新案ブランチを切る最小の自動PRフロー案（設計メモ）を作成する（owner: 啓、期限: 2025-12-07 目安）。
- [ ] **T-WF-1:** Sho v1 Debug ワークフローを定常運用に組み込む（Actions 起動・アサイン・レビュー動線の整備）（owner: 啓、期限: 2025-12-07 目安）。

## レイヤーB（記録・構造化ループ）のゴールとステップ

**ゴール（Layer B）**

- 実行力は人間や外部システムに任せたまま、PM Kai が「実行提案 →（人間による実行）→ 実行結果の記録案 → 更新された実行提案」という記録ループを、自分で回せる状態にする。
- 具体的には、実行後の状態変化を踏まえた STATE / weekly / pm_snapshot の更新
