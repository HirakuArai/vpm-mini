# STATE: hakone-e2 / current_state

最終更新: 2025-11-23 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- vpm-mini 側で PM Kai v1（GitHub + LLM）のベースラインが整い、**2つ目のプロジェクトとして hakone-e2 を VPM に載せ始めた**段階。
- `project_definition.md` に目的・スコープ・成功条件の初期定義が完了。加えて、2026年箱根E²スペースに向けた**素材収集方針とチャンク化仕様 v0**を定義し、scene JSON（world_event / info_event + semantic_label）で扱う方向を決めた。
- 初期データスコープとして**「2026サイクル（出雲・全日本・予選会〜箱根本戦）」**を対象に、約50件の scene を `scenes_hakone_2026_v0.json` にまとめる計画を置いた（具体のシーン化はこれから）。
- hakone-e2 用の pm_snapshot は未実行で、weekly は 2025-11-23 版が最新。

### 1.2 Goals（G: ゴール）

**短期（〜数週間）**

- hakone-e2 用の PM Kai が、次の2点を説明できる状態にする：
  - 「このプロジェクトの目的・スコープ・成功条件（project_definition）」
  - 「いまの C/G/δ と Next 3（STATE + weekly ベース）」
- 箱根駅伝の **ごく限られた数の「イベント＋感情」ペア（例: 1大会の中の1〜2場面）** について、簡単な意味付けのメモを残す。

**中期（〜数ヶ月）**

- 箱根駅伝に関する 3〜5 個程度の「試合展開イベント → 意味・感情の解釈」を整理し、
  - それぞれが **どのような視点（選手／チーム／ファン／メディア）からどう意味を持つか**
  を説明できるようにする。
- そこから得られた洞察を、vpm-mini 側の EG-Space / 5セル設計（意味軸・座標系・観測の仕方）にフィードバックし、「スポーツ×感情」という具体例から汎用的な設計指針を抽出する。

### 1.3 Gap（δ: ギャップ）

- 初期データスコープは仮置きできた一方で、**最初の1〜2件の具体シーン選定と優先順位付け**が未着手。
- scene JSON の基本形は定まったが、**意味・感情タグの語彙・強度スケール・観点（選手/チーム/ファン/メディア）のガイドライン v0**が未整備。
- **ファイル運用（パス/命名規則/版管理/レビュー手順）**と、最小の記入テンプレート確定が未了。
- hakone-e2 の **pm_snapshot の初回実行がまだ**で、STATE/weekly と Next3 の同期検証ができていない。
- vpm-mini へのフィードバック形式（どの抽象化軸・メモ構造で返すか）が曖昧。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [ ] H2-PDEF-1: `docs/projects/hakone-e2/project_definition.md` をベースに、啓の頭の中にある「箱根E²構想」を言葉として肉付けする（目的・背景・なぜ箱根駅伝なのか）。
- [ ] H2-DATA-1: 最初に扱う具体シーン（1〜2件）を決める。注: 初期ターゲットは「2026サイクル（出雲・全日本・予選会〜本戦）」に仮置き済み。
- [x] H2-FORMAT-1: 「イベント＋感情」をどう表現するかのミニフォーマット（scene JSON: world_event / info_event + semantic_label）と、素材収集・チャンク化仕様 v0 を定義した。
- [ ] H2-PM-1: hakone-e2 に対して pm_snapshot（project_id=hakone-e2）を1回実行する（weekly 2025-11-23 は作成済み）。
- [ ] H2-DATA-2: `data/hakone-e2/scenes_hakone_2026_v0.json` のスケルトンを作成し、最初の 5〜10 件を記入する（レビュー用）。
- [ ] H2-GUIDE-1: 意味・感情タグのガイドライン v0 を1ページ作成（観点、語彙、強度スケール、例付き）。
- [ ] H2-OPS-1: データファイル運用ルール（命名/パス/版管理/レビュー）を短いメモとして定義する。

## 3. Evidence Links（証拠リンク）

- プロジェクト定義:
  - `docs/projects/hakone-e2/project_definition.md`
- STATE:
  - `STATE/hakone-e2/current_state.md`（本ファイル）
- 週次レポート:
  - `reports/hakone-e2/2025-11-23_weekly.md`（初期テンプレ＋最初のメモ）
- vpm-mini 側の関連文脈:
  - `docs/pm/pm_snapshot_v1_spec.md`
  - `docs/pm/layer_b_update_flow.md`
  - `STATE/vpm-mini/current_state.md`

[STATE/hakone-e2/current_state.md ここまで]
