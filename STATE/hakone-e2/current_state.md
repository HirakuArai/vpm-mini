# STATE: hakone-e2 / current_state

最終更新: 2025-11-23 by 啓

## 1. Snapshot（C / G / δ）

### 1.1 Current（C: 現在地）

- vpm-mini 側で PM Kai v1（GitHub + LLM）のベースラインが整い、**2つ目のプロジェクトとして hakone-e2 を VPM に載せ始めた**段階。
- 本プロジェクトの目的・スコープ・成功条件は `docs/projects/hakone-e2/project_definition.md` に初期版が定義されたばかりで、具体的なデータ整理や意味付けはまだ手つかず。
- これまでの会話の中で、
  - 箱根駅伝を使って「感情を含んだ EG-Space を試す」
  - その経験を vpm-mini / EG-Space 設計にフィードバックする
  という構想は共有済みだが、まだプロジェクトとしての「C/G/δ / Next 3」は明文化されていない。

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

- 箱根駅伝のどの大会・どの場面を対象とするか（データのスコープ）がまだ決まっていない。
- 「イベント（何が起きたか）」と「意味・感情（どう感じたか／どう解釈できるか）」をどう表現するか（フォーマット・粒度）が未定義。
- hakone-e2 用の weekly や PM Snapshot をまだ一度も回しておらず、PM としての C/G/δ / Next 3 が具体化できていない。
- vpm-mini へのフィードバックの形（どういうメモや構造で返すのがよいか）が曖昧。

## 2. Active Focus / Tasks（いまフォーカスしている課題）

- [ ] **H2-PDEF-1:** `docs/projects/hakone-e2/project_definition.md` をベースに、啓の頭の中にある「箱根E²構想」を言葉として肉付けする（目的・背景・なぜ箱根駅伝なのか）。
- [ ] **H2-DATA-1:** 最初に扱う大会／場面を 1〜2 個決める（例: ある年の往路〇区の逆転シーンなど）。
- [ ] **H2-FORMAT-1:** 「イベント＋感情」をどう表現するかのミニフォーマット（テキスト構造）を試作する。
- [ ] **H2-PM-1:** hakone-e2 に対して初回の weekly（2025-11-23 分）を書き、pm_snapshot（project_id=hakone-e2）を1回実行する。

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
