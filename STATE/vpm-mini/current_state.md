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

### 1.3 Gap（δ: ギャップ）

- PM Kai v1 の **入出力フォーマット（プロンプトと回答形式）がまだ固まっていない**。
- `STATE/vpm-mini/current_state.md` や週次レポートに、**実際の C/G/δ / Next 3 が継続的に書き込まれている状態**にはまだ至っていない。
- 他プロジェクト向けの `docs/projects/<project_id>/project_definition.md` や `STATE/<project_id>/current_state.md` が未整備。
- VM/GKE コスト縮退は一度完了したが、今後のための「月次インベントリレポート」などの軽い見張り仕組みは未設計。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [ ] **T-PM-1:** PM Kai v1 の「標準質問」と「回答フォーマット（C/G/δ + Next 3 + Evidence）」を定義する。
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
