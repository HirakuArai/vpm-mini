# PM Snapshot Layer B Flow v1 Draft

repo = vpm-mini / phase = Phase 2  
version = pm_snapshot_layerb_flow_v1_draft

このドキュメントは、`PM Snapshot (vpm-mini)`（Gen）の出力を起点にして、  
`STATE/current_state.md` や `reports/*_weekly.md` を更新する **Layer B（記録・構造化）サイクル**の v1 ドラフトを定義する。

Doc Update レーン（Aya↔Sho↔apply）とは別に、

- Gen（PM Snapshot） → Kai / Human → Codex → STATE/weekly

という **pm_snapshot レーンの Layer B** を明文化し、  
将来の自動化（最小自動PRフロー）に備える。

> ここでは主に vpm-mini / project_id=vpm-mini を対象とする。

---

## 1. 目的

- `PM Snapshot (vpm-mini)` の出力（C/G/δ/Next3）を起点に、
  - STATE/current_state.md の C/G/δ / Active Tasks / Evidence
  - reports/vpm-mini/*_weekly.md
  を **人間が理解しやすい形で更新する最小サイクル**を定義する。
- これにより、Gen（PM Snapshot）の役割（今と次の整理）と、
  Doc Update / Sho / Apply のレーンとの関係を明確にする。

---

## 2. 役割と責務（pm_snapshot レーン）

- **Gen（PM Snapshot / snapshot_pm / display_name: Gen）**
  - 入力: SSOT（project_definition / STATE / weekly / pm系docs）
  - 出力: `pm_snapshot_v1` JSON + Markdown
  - 責務: C/G/δ と Next3 を「PM視点」で整理する。

- **Kai（meta_pm / display_name: Kai）+ Human（啓＋ChatGPT）**
  - 入力: 最新の pm_snapshot_v1（Genの出力）
  - 出力: STATE/weekly に対する「更新案テキスト」（差分の説明）
  - 責務: Snapshot の内容をもとに「どこを STATE/weekly に書き換えるべきか」を言語化する。
  - 当面は Kai = ChatGPT（このプロジェクトのメタPM）として扱う。

- **Apply（Codex + PR）**
  - 入力: Kai/Human が書いた更新案テキスト
  - 出力: STATE/weekly を更新する PR
  - 責務: ファイルを編集し、PR として反映する（STATE/current_state.md / reports/*_weekly.md）。

- **Human gate（啓）**
  - 入力: Snapshot / 更新案 / PR diff
  - 出力: 採否（PRを merge するかどうか）
  - 責務: 最終的な採否判断と、必要に応じた手直し。

Doc Update レーン（Aya↔Sho↔apply）とは異なり、  
この pm_snapshot レーンでは **Gen の出力と STATE/weekly の整合性**にフォーカスする。

---

## 3. 入力と出力

### 3.1 入力

- `pm_snapshot_v1` JSON + Markdown（Gen の最新出力）
  - C（Current）
  - G（Goals）
  - δ（Gaps）
  - Next 3
  - Evidence

- 現時点の SSOT：
  - `docs/projects/vpm-mini/project_definition.md`
  - `STATE/vpm-mini/current_state.md`
  - `reports/vpm-mini/*_weekly.md`
  - その他 pm 系 docs（roles_v1 / blackboard_v1_draft 等）

### 3.2 出力

- 更新された:
  - `STATE/vpm-mini/current_state.md`
    - C/G/δ / Active Tasks / Evidence
  - `reports/vpm-mini/YYYY-MM-DD_weekly.md`
- 必要であれば:
  - pm 系 docs（設計変更があった場合）

各更新は必ず PR 経由（Codex）で行い、Evidenceとして PR 番号を残す。

---

## 4. Flow v1（人力＋Codex版）

v1 では、pm_snapshot レーンの Layer B Flow を次のように回す。

### Step 0: 前提

- Gen が `PM Snapshot (vpm-mini)` を実行し、  
  最新の `pm_snapshot_v1` を Artifact + `reports/pm_snapshot` 等に保存している。
- SSOT（STATE / project_definition / weekly）が main に反映済み。

### Step 1: Gen（PM Snapshot）

1. 啓が Actions UI から `PM Snapshot (vpm-mini)` を実行する。  
2. Gen は `pm_snapshot_v1` JSON + Markdown を生成し、C/G/δ/Next3 を出力する。
3. Snapshot は Artifact から取得し、Kai/Human が読む。

### Step 2: Kai + Human（更新案テキストを作る）

1. Kai（このチャット上のメタPM）＋啓が Snapshot を読み、  
   以下の観点で「どこを STATE/weekly に反映すべきか」を整理する：
   - C に反映すべき「新しい現状」
   - G に反映すべき「目標の更新」
   - δ に反映すべき「未解決のギャップ」
   - Active Tasks / Next 3 に反映すべきタスクの追加・更新
   - Evidence に追加すべき PR / docs

2. Kai が更新案テキスト（人間が読める diff 説明）を作る：
   - 例:
     - 「STATE/current_state.md の Current セクションを Snapshot のCに合わせて書き換える」
     - 「Gap に `pm_snapshot レーンの Layer B サイクル未実装` を追加」
     - 「Next 3 に `pm_snapshot レーンの最小サイクルを1回回す` を追加」
     - 「Evidence に最新の Snapshot や PR を追記」

### Step 3: Apply（Codex + PR）

1. Kai が用意した更新案テキストを Mac 側の Codex に渡す（このプロジェクトで普段やっているスタイル）。
2. Codex は更新案に従って:
   - `STATE/vpm-mini/current_state.md`
   - `reports/vpm-mini/*_weekly.md`
   を編集する。
3. Codex は変更を commit し、適切なブランチ名（例: `apply/pm-snapshot-layerb-YYYYMMDD`）で PR を作成する。

### Step 4: Human gate（啓）

1. 啓が PR の diff を閲覧し：
   - Snapshot に書かれている C/G/δ/Next3 と整合しているか
   - 不自然な削除／追加がないか
   を確認する。
2. 啓が PR を merge することで、pm_snapshot レーンの Layer B 更新が state に反映される。
3. 必要なら、次の Snapshot（Gen）実行時に C/G/δ/Next3 の更新を確認する。

---

## 5. Doc Update レーンとの関係（高レベル）

現時点では、レイヤーBには大きく2つのレーンが存在する：

- **Doc Update レーン（Aya↔Sho↔apply）**
  - 入力: progress_summary + SSOT
  - 出力: `doc_update_proposal_v1` / `doc_update_review_v1` 経由で STATE/weekly を更新
  - 視点: 「進捗から見た具体的なドキュメント修正案」

- **pm_snapshot レーン（Gen↔Kai/Human↔apply）**
  - 入力: `pm_snapshot_v1`（C/G/δ/Next3）
  - 出力: STATE/weekly の C/G/δ/Next3 の整合性調整
  - 視点: 「PMとしての全体像とギャップを埋める更新」

v1 の段階では、両レーンは次のように使い分ける：

- 新しい進捗や特定機能に関する修正 → Aya（Doc Update）＋Sho ルート
- プロジェクト全体の C/G/δ/Next3 の整合性や「そもそも何を優先すべきか」の見直し → Gen（pm_snapshot）ルート

将来的には、両レーンの出力が STATE/weekly 上で自然に重なり合うよう、  
Kai（meta_pm）がバランスを取る。

---

## 6. 今後の拡張ポイント（v2以降）

- pm_snapshot レーンでも、doc_update レーンのような「board（駅の黒板）」連携を持たせる：
  - Gen → Aya に「次に doc_update してほしい候補」を黒板に書く、など。
- pm_snapshot レーンからの更新提案を JSON 形式で表現する（`snapshot_update_proposal_v1` のような構造）。
- Snapshot → STATE/weekly の反映を、Doc Update レーンとの重複を避けながら最小自動PRフローとして実装する。

本ドキュメントは **pm_snapshot_layerb_flow_v1_draft** として保持し、  
実際の運用（vpm-mini での1〜2サイクルの試行）を踏まえて改訂した上で、正式版 `pm_snapshot_layerb_flow_v1` を別途切り出す。
