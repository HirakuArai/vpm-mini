# Blackboard Core Spec v1  
（Doc Update レーン向けコア仕様）

## 1. 目的とスコープ

本ドキュメントは、Virtual Project Manager (VPM) プロジェクトにおける  
**「黒板 (blackboard) entry」** の共通フォーマットとライフサイクルを定義する。

ここで定義するのは、あくまで「コア仕様」であり、

- フィールド構造（必須／任意）
- ステータス（status）の種類と遷移
- 現時点での保存・受け渡し方法（GitHub Issue コメント）

に限定する。

各ロール（Aya / Sho / Tsugu / Gen / Hana など）が

- どの kind の entry を読み取るか
- どの条件で entry を書き込むか

といった「役割ごとの契約」は、別ドキュメント  
`docs/pm/blackboard_roles_contract_v1.md` で定義する。

本 spec v1 の主な適用対象は、まず **Doc Update レーン** である：

- 僕ら → Aya → Sho → Tsugu → Gen → 僕ら  
  の 1 巡（ぐるり）において、黒板 entry の「型」を共通化する。

---

## 2. データモデル（entry のフィールド）

### 2.1 全体像

黒板 entry は、以下のフィールドを持つ JSON オブジェクトとする。

必須フィールド：

- `id: string`
- `from: string`
- `to: string`
- `project_id: string`
- `kind: string`
- `status: string`
- `payload: object`
- `target_docs: array`
- `created_at: string`
- `updated_at: string`

任意フィールド（v1 推奨）：

- `source_issue: number | string`  
  （紐づく GitHub Issue 番号）
- `source_comment_id: number | string`  
  （紐づく GitHub コメント ID）
- `source_run_id: number | string`  
  （紐づく GitHub Actions の run_id）
- `note: string`  
  （補足メモ）

### 2.2 各フィールドの定義

#### id

- 型: `string`
- 要件:
  - 黒板 entry ごとに **一意** であること。
  - 生成方法はレーンごとの実装に委ねるが、少なくとも  
    `project_id` と `source_issue` / `source_run_id` 等と組み合わせて  
    衝突を避けること。

例：

- `"vpm-mini-docupdate-issue571-1"`
- `"vpm-mini-apply-run19793359086"`

#### from

- 型: `string`
- この entry を **書いた actor 名**。
- 例：
  - `"Human"`
  - `"Aya"`
  - `"Sho"`
  - `"Tsugu"`
  - `"Gen"`

#### to

- 型: `string`
- この entry の **主な宛先となるロール名**。
- 例：
  - `"Aya"`
  - `"Sho"`
  - `"Tsugu"`
  - `"Gen"`
  - `"Hana"`
  - `"Human"`

ロールごとに、`to` と `kind` を組み合わせた pick ルールを  
`blackboard_roles_contract_v1` 側で定義する。

#### project_id

- 型: `string`
- 対象となるプロジェクト ID。
- 例：
  - `"vpm-mini"`
  - `"hakone-e2"`

ロールは基本的に、`project_id` も含めてフィルタしたうえで  
「自分の仕事とみなす entry」を決定する。

#### kind

- 型: `string`
- entry が表す **処理の種類** を示す識別子。
- 例（Doc Update レーン）：
  - `"doc_update_proposal_request"`
  - `"doc_update_review_request"`
  - `"doc_update_apply_request"`
  - `"doc_update_error"`

`kind` ごとの意味・ペイロード構造は  
`blackboard_roles_contract_v1` または専用 spec で定義する。

#### status

- 型: `string`
- entry の現在の状態を表す。

v1 では以下の enum を定義する：

- `"open"`:  
  宛先ロールがまだ処理していない状態（未着手）。
- `"in_progress"`:  
  宛先ロールが処理中であることを示す任意状態（v1 では必須ではない）。
- `"done"`:  
  宛先ロールによる処理が完了し、この entry として対応済み。
- `"error"`:  
  処理に失敗した・payload が不正など、異常終了を表す。
- `"canceled"`:  
  人間または上位ロールの判断で、この entry 自体が不要になった状態。

v1 では、Doc Update レーンにおいて最低限以下を扱う：

- Human → Aya 宛: `status = "open"` で作成。
- Tsugu → （誰か）宛: 処理完了後に `status = "done"` へ更新。
- エラー発生時: `status = "error"` の entry を別途作成してもよい。

#### payload

- 型: `object`
- entry に紐づく **内容本体** を格納する入れ物。

`payload` の **中身の構造** は `kind` ごとに異なり、  
各 kind の spec で定義する（例：doc_update 用 payload）。

v1 では、Doc Update レーン向けに最低限次のようなフィールドを想定する：

- `summary: string`  
  人間がパッと見て分かる要約。
- `details: object`  
  kind 固有の詳細情報。
- `refs: object`  
  関連するファイルパス・Issue 番号・run_id などの参照。

ただし、ここではあくまで「object であり、kind ごとに定義される」という  
コア仕様のみを定める。

#### target_docs

- 型: `array`
- この entry が対象とする **ドキュメント（ファイル / セクション）** のヒント。

v1 では、次の 2 形態のどちらかとする：

1. 単純にパスの配列：

   ```json
   "target_docs": [
     "STATE/current_state.md",
     "docs/pm/pm_snapshot_v1_spec.md"
   ]
   ```

2. オブジェクトの配列：

   ```json
   "target_docs": [
     {
       "path": "STATE/current_state.md",
       "section": "## 差分（δ）"
     }
   ]
   ```

Doc Update レーン v1 では、パスの配列から始め、
必要に応じてセクション指定などを追加する。

created_at / updated_at

型: string

ISO 8601 形式の日時文字列（タイムゾーン付き）を推奨する。

例：

"2025-11-30T02:30:00+09:00"

created_at:

entry が最初に作られた時刻。

updated_at:

status や payload が変更された 最新の時刻。

## 3. ステータスとライフサイクル

### 3.1 基本的な遷移

v1 では、次のようなシンプルなライフサイクルを前提とする：

open → in_progress → done

open → error

in_progress → error

open → canceled

in_progress → canceled

Doc Update レーンの最小パターン：

Human（または上位ロール）が、

status = "open"

to = "Aya"

kind = "doc_update_proposal_request"
で entry を作成する。

Aya の workflow がこの entry を拾い、  
処理完了後に（必要であれば）status = "done" に更新するか、  
次のロール宛の新しい entry を作成する。

Sho / Tsugu も同様に、それぞれの役割に応じて entry を新規作成・更新する。

Tsugu が PR マージまで完了した段階で、  
元の entry もしくは対応する entry の status = "done" に更新する。

### 3.2 誰が status を更新してよいか

原則として、from または to に関係するロール（＋Human）のみが  
status を変更する。

GitHub 上の実装では、

対応する workflow（Aya / Sho / Tsugu）が  
黒板 entry の status を更新するステップを持つ。

人間（啓）が手動で canceled に変更するケースも許容する。

## 4. 表現と保存方法（v1 実装）

### 4.1 GitHub Issue コメントとしての表現

v1 では、黒板 entry は GitHub Issue コメントに埋め込む。

Doc Update レーンの現行フォーマット（例）：

<!-- blackboard:doc_update_v1 -->

json
{ ... ここに JSON オブジェクト ... }

ルール：

1 行目: HTML コメントで黒板種別を示す。

例: <!-- blackboard:doc_update_v1 -->

2 行目: 空行。

3 行目: json という文字列（種別マーカー）。

4 行目以降: ダブルクォートのみを使った JSON オブジェクト 1 つ。

この JSON オブジェクトが、本 spec v1 で定義した  
「黒板 entry のデータモデル」に対応する。

### 4.2 パーサの前提

黒板を読む側（Aya など）は、次の流れで entry を取得する：

対象 Issue のコメントを列挙する。

<!-- blackboard:doc_update_v1 --> で始まるコメントを検出する。

その直後の json 行の次行から、末尾までを JSON として読み取る。

JSON をパースし、本ドキュメントで定義したフィールドを前提に処理する。

## 5. 適用範囲と今後の拡張

### 5.1 v1 の適用範囲

プロジェクト: まずは vpm-mini

レーン: Doc Update レーン（黒板を起点にした Aya → Sho → Tsugu → Gen の一巡）

この範囲で、黒板 entry の「型」が安定して使えることを目指す。

### 5.2 今後の拡張の方向性（メモ）

v1 では、

ロールごとの allowed_kinds

kind ごとの payload schema

などは別ドキュメント（roles contract / 各 kind の spec）に切り出す。

黒板の役割を Doc Update 以外にも広げる場合は、

共通フィールドは本 spec v1 を再利用

kind / payload / roles contract を追加定義

という方針で拡張していく。
