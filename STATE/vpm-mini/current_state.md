# STATE: vpm-mini / current_state

最終更新: 2025-11-23 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- フェーズ: Phase 2。インフラ（VM/GKE）を一旦縮退し、「GitHub + LLM の PM Kai v1」にフォーカスしている。
- プロジェクトの SSOT は `docs/projects/vpm-mini/project_definition.md` に定義済み（PR #800）。`STATE/vpm-mini/current_state.md` と `reports/vpm-mini/2025-11-23_weekly.md` に 2025-11-23 時点の C/G/δ と進捗を記録（PR #801, #802, #803, #810）。
- `docs/pm/pm_snapshot_v1_spec.md` に pm_snapshot_v1 の仕様と標準質問を定義し、`.github/workflows/pm_snapshot.yml` から手動実行で Snapshot を生成可能（PR #804, #805, #806, #807, #809）。
- レイヤーB最小更新フロー v1 を `docs/pm/layer_b_update_flow.md` に定義。加えて、`docs/pm/doc_update_pipeline_v1.md` と `docs/pm/doc_update_review_v1_spec.md` を追加し、doc_update_proposal_v1 の提案〜レビューの枠組みを整備。Codex 用の適用ブリーフ `docs/ops/codex_brief_apply_doc_update_v1.md` も用意（PR #817, #818）。これらを前提に、vpm-mini 自身でも doc_update_proposal_v1 による STATE / weekly 更新案の提示を開始する方針。
- GCP 側は devbox-codex VM 停止、GKE Autopilot クラスタ `vpm-mini` と不要 PVC を削除済みで、将来実験用の最小構成（ディスクのみ）に縮退。

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
- Kai による STATE/weekly の差分提案を doc_update_proposal_v1 JSON として起票し、doc_update_review_v1_spec に従ってレビューする手順は設計済みだが、運用ルール（トリガー、責任分担、採否基準）が明文化されていない。
- PR 自動化（pm_snapshot 実行直後に更新案ブランチを作成する最小フロー）の設計と検証が未完。
- マルチプロジェクト展開に向けた他プロジェクトの project_definition / STATE / reports 整備は未着手（hakone-e2 は試行のみ）。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [x] **T-PM-1:** PM Kai v1 の標準質問と出力フォーマット（pm_snapshot_v1 + Markdown）を定義し、spec に追記する（PR #809 完了）。
- [ ] **T-STATE-1:** この current_state を 2025-11-23 ベースラインとして確定し、C/G/δ と Active Tasks を「数週間はそのまま使える」レベルまで整える（layer_b_update_flow への参照を追記）。
- [ ] **T-PM-2:** `/ask` + GitHub Actions による STATE / weekly 更新ループの設計を進める（pm_snapshot の結果から STATE/weekly 更新案を生成する最小フロー案）。
- [ ] **T-PM-3:** 他プロジェクト（例: 箱根E² or 会社業務）について、最初の `project_definition` / `STATE` / `weekly` を用意し、pm_snapshot を回してみる（hakone-e2 で doc_update_proposal_v1 → STATE/weekly の1サイクル試行済み）。
- [ ] **T-PM-4:** vpm-mini で Kai による「STATE/weekly 更新案（テキスト）」生成 → 手動PR の最小サイクルを1回実施して検証する。
- [ ] **T-INF-1:** VM/GKE 縮退後の GCP インベントリを月次レベルで確認する軽い仕組み（レポート or 手動チェック）を検討する（優先度はレイヤーBより低い）。
- [ ] **T-DOC-1:** doc_update_proposal_v1 を vpm-mini に適用し、STATE/weekly 更新案 → 手動PR → マージの1サイクルを実施する（docs/pm/doc_update_pipeline_v1.md・docs/pm/doc_update_review_v1_spec.md に準拠。適用には `docs/ops/codex_brief_apply_doc_update_v1.md` を使用）（優先度: 高）

## レイヤーB（記録・構造化ループ）のゴールとステップ

**ゴール（Layer B）**

- 実行力は人間や外部システムに任せたまま、PM Kai が「実行提案 →（人間による実行）→ 実行結果の記録案 → 更新された実行提案」という記録ループを、自分で回せる状態にする。
- 具体的には、実行後の状態変化を踏まえた STATE / weekly / pm_snapshot の更新案を Kai が出し続け、人間がそれをレビューしてマージする運用を確立する。

**大まかなステップ**

1. **B-1: 現状のパターンを STATE に明文化する**

   - 「実行があったら pm_snapshot を回し、その結果を見ながら STATE / weekly を更新する」というパターンを、vpm-mini の公式フローとして STATE に書き残す（本ファイルの更新で進行中）。

2. **B-2: PM Snapshot から STATE 更新案を生成する仕組みを構想する**

   - pm_snapshot_v1 の JSON / Markdown を入力に、「STATE/current_state.md の C/G/δ と Active Tasks をこう変えるべき」という差分案（patch）を Kai に生成させるイメージを固める。
   - 最初は「提案テキストだけ」でよく、PR 化は後段で構わない。

3. **B-3: STATE 更新案を PR として出すミニワークフローを設計する**

   - 手動トリガ（workflow_dispatch）で、
     1) 最新 pm_snapshot を取得  
     2) Kai に STATE 更新案を生成させる  
     3) STATE/vpm-mini/current_state.md を更新する PR を作成  
     という最小ループの設計案を作る。
   - マージは必ず人間が行う前提にしておく。

4. **B-4: vpm-mini でレイヤーBループを1サイクル回して検証する**

   - 何か実行（または決定）があったタイミングで、
     1) pm_snapshot を実行  
     2) B-3 のワークフローで STATE 更新PRを出す  
     3) 啓が内容をレビューしてマージ  
   - このサイクルを 1 回以上回し、「このやり方なら PM Kai に記録を任せていけそうだ」と判断できるか確認する。

## 3. Evidence Links（証拠リンク）

- プロジェクト定義:
  - `docs/projects/vpm-mini/project_definition.md`（PR #800）
- STATE:
  - `STATE/vpm-mini/current_state.md`（本ファイル。PR #801, #803, #808, #810 等で更新）
- 週次レポート:
  - `reports/vpm-mini/2025-11-23_weekly.md`（PR #802, #803, #810）
- PM仕様:
  - `docs/pm/pm_snapshot_v1_spec.md`（PR #804, #809）
- PM Snapshot ワークフロー:
  - `.github/workflows/pm_snapshot.yml`（PR #805, #806, #807）
- インフラ縮退:
  - GCP 操作ログ（別セッションの記録）および STATE の記述に準拠。
- レイヤーB更新フロー設計:
  - `docs/pm/layer_b_update_flow.md`
- ドキュメント更新パイプライン:
  - `docs/pm/doc_update_pipeline_v1.md`（PR #817）
  - `docs/pm/doc_update_review_v1_spec.md`（PR #817）
- Codex ブリーフ:
  - `docs/ops/codex_brief_apply_doc_update_v1.md`（PR #818）
