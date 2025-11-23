# STATE: vpm-mini / current_state

最終更新: 2025-11-23 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- フェーズ: Phase 2。インフラ（VM/GKE）を一旦縮退し、**「GitHub + LLM の PM Kai v1」** にフォーカスする方針に切り替えた。
- `docs/projects/vpm-mini/project_definition.md` に、vpm-mini の目的・制約・成功条件・現フェーズの位置づけが SSOT として定義されている（PR #800）。
- `STATE/vpm-mini/current_state.md` と `reports/vpm-mini/2025-11-23_weekly.md` に、2025-11-23 時点の C/G/δ と今週の進捗・Next3 が記録されている（PR #801, #802, #803, #810）。
- `docs/pm/pm_snapshot_v1_spec.md` に、PM Kai v1 の出力仕様（pm_snapshot_v1）と標準質問（Standard Prompt）が定義されており、Actions 上で `pm_snapshot.yml` を手動実行すると PM Snapshot を生成できる状態になっている（PR #804, #805, #806, #807, #809）。
- GCP 側では devbox-codex VM を停止し、GKE Autopilot クラスタ `vpm-mini` と不要な PVC ディスクを削除して、将来の実験用の最小構成（ディスクのみ）に縮退済み（インフラコストはほぼゼロ）。

### 1.2 Goals（G: ゴール）

**短期（〜数週間）**

- PM Kai v1 が、GitHub 上の情報（project_definition / STATE / reports / Issue / PR）だけを読んで、**いつでも vpm-mini の C/G/δ と Next 3 を一貫した形で答えられる状態**にする。
- vpm-mini 用 PM Kai v1 を、他プロジェクトにも展開可能な PM エンジンとして使えるよう、`project_id` 前提の構造と pm_snapshot_v1 仕様を安定させる。
- レイヤーB（記録・構造化ループ）の 1 サイクルを、vpm-mini で実際に回し、「このパターンなら続けられそう」と判断できるレベルまで持っていく。

**中期（〜数ヶ月）**

- 箱根E² や会社業務プロジェクトにも、`docs/projects/<project_id>/project_definition.md`・`STATE/<project_id>/current_state.md`・`reports/<project_id>/..._weekly.md` を整備し、**「マルチプロジェクト VPM」として PM を立てられる状態**にする。
- EG-Space と 5セルを「論理的な視点／座標」として PM Kai に組み込み、物理インフラに依存せずに C/G/δ・Next3 の精度を高める検証を進める。
- レイヤーB（記録・構造化）の最小ループ（PM Snapshot → STATE/weekly 更新案 → PR → マージ）を vpm-mini で安定運用し、必要に応じて他プロジェクトにも展開できる設計にする。

### 1.3 Gap（δ: ギャップ）

- pm_snapshot_v1 の仕様と標準質問は定義されたが、**STATE / weekly / pm_snapshot をどう自動的に更新・連携させるか（レイヤーBの運用フロー）がまだ具体化されていない**。
- `STATE/vpm-mini/current_state.md` や weekly が、現状は主に手動更新であり、PM Snapshot からの更新案生成〜PR 作成の流れは未実装。
- 他プロジェクト用の `project_definition` / `STATE` / `reports` が未整備で、vpm-mini 以外のプロジェクトについては PM Kai のカバー範囲に入っていない。
- PM Kai v1 を「週次の儀式」にどう組み込むか（pm_snapshot の実行タイミングと、どの程度 Next3 に従うか）の運用ルールがまだ仮置きである。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [x] **T-PM-1:** PM Kai v1 の標準質問と出力フォーマット（pm_snapshot_v1 + Markdown）を定義し、spec に追記する（PR #809 完了）。
- [ ] **T-STATE-1:** この current_state を 2025-11-23 時点のベースラインとして調整し、C/G/δ と Active Tasks を「数週間はそのまま使える」レベルまで整える（今回の編集で進行中）。
- [ ] **T-PM-2:** `/ask` + GitHub Actions による STATE / weekly 更新ループの設計を進める（pm_snapshot の結果から STATE 更新案を生成し PR にする最小フローの案を作る）。
- [ ] **T-PM-3:** 他プロジェクト（例: 箱根E² or 会社業務）について、最初の `project_definition` / `STATE` / `weekly` を用意し、pm_snapshot を回してみる。
- [ ] **T-INF-1:** VM/GKE 縮退後の GCP インベントリを月次レベルで確認する軽い仕組み（レポート or 手動チェック）を検討する（優先度はレイヤーBより低い）。

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
