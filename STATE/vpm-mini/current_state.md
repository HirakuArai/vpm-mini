# STATE: vpm-mini / current_state

最終更新: 2025-11-23 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- Phase 2 にいるが、当面の優先フォーカスを **「PM Kai v1（GitHub + LLM のみ）」** に絞る方針に切り替えた。
- プロジェクトの目的・制約・成功条件を `docs/projects/vpm-mini/project_definition.md` として SSOT 化済み（PR #800）。
- `STATE/vpm-mini/current_state.md` のスキャフォールドを追加し、C/G/δ とアクティブ課題を書く器を用意した（PR #801）。
- 週次レポートのテンプレートを `reports/vpm-mini/2025-11-23_weekly.md` に追加し、「事実ログの器」ができた（PR #802）。
- VM / GKE / 5セル物理分散・自律実行は「上位フェーズ」に送る方針で合意し、インフラ側の検討は一時的にペンディング中。
- GCE 側では devbox-codex VM を停止（TERMINATED）し、GKE Autopilot クラスタ `vpm-mini` および不要な PVC ディスクを削除して、ほぼゼロコスト状態に縮退済み。

### 1.2 Goals（G: ゴール）

**短期（〜数週間）**

- PM Kai v1 が、GitHub 上の情報（project_definition / STATE / reports / Issue / PR）だけを読んで、
  **いつでも C/G/δ と Next 3 を一貫した形で答えられる状態**にする。
- vpm-mini 用の PM Kai v1 を「他プロジェクトに横展開可能な PM エンジン」として使えるよう、構造（project_id 前提のレイアウト）を固める。

**中期（〜数ヶ月）**

- 別プロジェクト（例: 箱根E² / 会社業務プロジェクト）にも `project_definition / STATE / reports` を整備し、
  **vpm-mini と同じ仕組みで PM を回せる「マルチプロジェクト VPM」状態**にする。
- EG-Space や 5セルを、まずは「論理的な視点・座標」として PM Kai の内部に導入し、物理インフラに依存しない形でテストする。
- PM Kai が「実行提案 →（人間による実行）→ 実行結果の記録案 → 更新された実行提案」というレイヤーBの記録ループを、vpm-mini で一通り回せる状態にする（STATE / weekly / pm_snapshot の更新案を Kai が継続的に出せるようにする）。

### 1.3 Gap（δ: ギャップ）

- PM Kai v1 の標準質問と出力フォーマットは spec に定義されたが、それを使った自動ループ（STATE/weekly 更新）や運用フローはこれから。
- `STATE/vpm-mini/current_state.md` や週次レポートに、**実際の C/G/δ / Next 3 が継続的に書き込まれている状態**にはまだ至っていない。
- 他プロジェクト向けの `docs/projects/<project_id>/project_definition.md` や `STATE/<project_id>/current_state.md` が未整備。
- VM/GKE コスト縮退は一度完了したが、今後のための「月次インベントリレポート」などの軽い見張り仕組みは未設計。

## レイヤーB（記録・構造化ループ）のゴールとステップ

**ゴール（Layer B）**

- 実行力は人間や外部システムに任せたまま、
  PM Kai が「実行提案 →（人間による実行）→ 実行結果の記録案 → 更新された実行提案」という記録ループを、自分で回せる状態にする。
- 具体的には、実行後の状態変化を踏まえた STATE / weekly / pm_snapshot の更新案を Kai が出し続け、人間がそれをレビューしてマージする運用を確立する。

**大まかなステップ**

1. **B-1: 現状のパターンを STATE に明文化する**

   - 「実行があったら pm_snapshot を回し、その結果を見ながら STATE / weekly を更新する」という今やっているパターンを、vpm-mini の公式フローとして STATE に書き残す。

2. **B-2: PM Snapshot から STATE 更新案を生成する仕組みを構想する**

   - pm_snapshot_v1 の JSON / Markdown を入力に、
     「STATE/current_state.md の C/G/δ と Active Tasks をこう変えるべき」という差分案（patch）を Kai に生成させるイメージを固める。
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

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [x] **T-PM-1:** PM Kai v1 の「標準質問」と「回答フォーマット（C/G/δ + Next 3 + Evidence）」を定義する（PR #809 で実行）。
- [ ] **T-PM-2:** `/ask` + GitHub Actions で、少なくとも週次で `STATE/vpm-mini/current_state.md` を更新提案できるワークフロー案を作る。
- [ ] **T-PM-3:** `reports/vpm-mini/2025-11-23_weekly.md` を実際の内容で埋めて、週次レポートの最初の1枚を完成させる。
- [ ] **T-INF-1:** VM/GKE コスト縮退の実績を STATE に記録し、将来のための簡易インベントリレポート（例: 月1回）をどう仕組み化するか検討する。

## 3. Evidence Links（証拠リンク）

- プロジェクト定義:
  - `docs/projects/vpm-mini/project_definition.md`（PR #800）
- STATE:
  - `STATE/vpm-mini/current_state.md`（本ファイル, PR #801）
- 週次レポート・テンプレ:
  - `reports/vpm-mini/2025-11-23_weekly.md`（PR #802）
- 関連 PR / Issue:
  - #800 Docs: add vpm-mini project definition
  - #801 State: add vpm-mini current_state scaffold
  - #802 Reports: add vpm-mini weekly template (2025-11-23)

## 4. Recent Decisions / Notes（直近の決定・メモ）

- 2025-11-23: 「VPMのコア（PMとしての頭脳）は GitHub + LLM だけで実現できる」という前提に立ち、Phase 2 の現実的ゴールを **PM Kai v1** に再定義。
- 2025-11-23: 実行力（自律デプロイなど）は「自律進化フェーズ」として切り離し、当面は扱わない方針で合意。
- 2025-11-23: VM / GKE / 5セル物理実装は「将来の実行環境」とし、現フェーズでは PM Kai の頭脳設計に集中することを優先。
- 2025-11-23: devbox-codex VM を停止し、GKE Autopilot クラスタ `vpm-mini` と不要な PVC ディスクを削除して、インフラコストをほぼゼロまで縮退。
