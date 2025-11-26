# Blackboard v1 Draft — 「駅の黒板」プロトコル

repo = vpm-mini / phase = Phase 2  
version = blackboard_v1_draft

このドキュメントは、VPM 内の人格（Kai / Aya / Gen / Sho / Tsugu / Haku / Hana / …）が  
お互いに依頼・通知・結果報告を行うための「共通の伝言板（Blackboard）」の v1 草案である。

イメージとしては「みんなが通る駅の黒板」であり、

- 誰でもそこにメモを書ける  
- 各人格は、自分宛のメモだけ拾って動くことができる  
- 過去のやりとりがログとして残る  

という前提で設計する。

> 本ドキュメントは draft であり、将来 `blackboard_v1` として正式版を別途切り出す。

---

## 1. 基本コンセプト

### 1.1 何のための「黒板」か

- 役割間の依頼・通知・結果報告を、「共通の場」に残すため。
- 個々の AI や人間が直接「君にこれやって」と言い合うのではなく、
  - Aya → 「Shoへ、〇〇をレビューしてね」
  - Sho → 「Ayaへ、結果はここに置いたよ」
  のようなメモを黒板に書く。
- 各人格は、自分に関係するメモだけを見て行動する。

### 1.2 プロトコルとしての狙い

- 通信手段を「黒板の読み書き」1種類に統一することで、
  - ツリー型（ルート経由）と
  - ネットワーク型（直接会話）
  のハイブリッド問題を簡略化する。
- 誰が誰に何を頼んだかが、Git リポジトリ上にログとして残る。
- 将来、Haku（Metrics）が「どのやりとりが詰まりやすいか」を分析できる。

---

## 2. 黒板の物理的な置き場（v1案）

v1 では、黒板を「1つの JSON Lines ファイル」として表現する案を採用する。

- パス案（例）:

  - reports/board/doc_update_board_v1.jsonl  
    Doc Update 関連（Aya / Sho / Tsugu）のメモ

  将来的には用途別に増やす可能性はある：
  - reports/board/ui_board_v1.jsonl （Hana 関連）
  - reports/board/meta_board_v1.jsonl （Kai / Haku 関連）など

- フォーマット:
  - 1行 = 1メッセージの JSON オブジェクト
  - 過去のメッセージは追記していく（後でアーカイブ方針を決める）

---

## 3. メッセージスキーマ v1

最小限、メッセージごとに次のフィールドを持つことを前提とする。

例（1エントリ）:

  {
    "id": "2025-11-24_vpm-mini_ayatosho_001",
    "from": "Aya",
    "to": "Sho",
    "project_id": "vpm-mini",
    "kind": "doc_update_review_request",
    "payload_ref": "reports/doc_update_proposals/2025-11-24-vpm-mini.json",
    "status": "open",
    "created_at": "2025-11-25T12:00:00+09:00"
  }

### 3.1 フィールド定義

- id (string, required)  
  メッセージを一意に識別する ID。  
  例: "2025-11-24_vpm-mini_ayatosho_001"

- from (string, required)  
  送信元のロール名（display_name ではなく、基本は Aya / Sho / Kai などの短い名前）。

- to (string, required)  
  宛先のロール名。  
  例: "Sho", "Tsugu", "Hana"

- project_id (string, required)  
  対象プロジェクト。  
  例: "vpm-mini", "hakone-e2"

- kind (string, required)  
  メッセージの種類。v1 では主に次を想定：

  - "doc_update_review_request" : Aya → Sho のレビュー依頼
  - "doc_update_review_result"  : Sho → Aya or Tsugu のレビュー結果通知

  将来:

  - "doc_update_apply_request"  : Human or Kai → Tsugu（apply していいよ）
  - "metrics_report_ready"      : Haku → Kai/Hana など

- payload_ref (string, required)  
  メッセージの対象となる情報の参照。
  例:
    - "reports/doc_update_proposals/2025-11-24-vpm-mini.json"
    - "artifacts://..."（Actions artifact への論理的参照）

- status (string, required)  
  メッセージの状態。v1 ではシンプルに：

  - "open"        : 未処理
  - "in_progress" : 処理中（必要なら）
  - "done"        : 完了
  - "canceled"    : キャンセル

- created_at (string, required)  
  作成日時（ISO 8601）。  
  例: "2025-11-25T12:00:00+09:00"

※ 将来、必要になれば updated_at / note / correlation_id 等を追加する。

---

## 4. Aya → Sho のやりとり（Doc Update Reviewer の例）

ここでは、Doc Update Proposal → Review の 1 ケースを黒板でどう表現するかを示す。

### 4.1 Aya が Sho にレビューを依頼するメモ

  {
    "id": "2025-11-24_vpm-mini_ayatosho_001",
    "from": "Aya",
    "to": "Sho",
    "project_id": "vpm-mini",
    "kind": "doc_update_review_request",
    "payload_ref": "reports/doc_update_proposals/2025-11-24-vpm-mini.json",
    "status": "open",
    "created_at": "2025-11-25T12:00:00+09:00"
  }

Aya の Workflow（Doc Update Proposal）が完了したタイミングで、  
このような 1 行を reports/board/doc_update_board_v1.jsonl に追記するイメージ。

### 4.2 Sho がレビューを完了したあとに書くメモ（案）

  {
    "id": "2025-11-24_vpm-mini_shotoaya_001",
    "from": "Sho",
    "to": "Aya",
    "project_id": "vpm-mini",
    "kind": "doc_update_review_result",
    "payload_ref": "artifacts://doc_update_review_v1_vpm-mini_2025-11-25.json",
    "status": "done",
    "created_at": "2025-11-25T12:10:00+09:00"
  }

ここでの payload_ref は、Sho の Workflow が生成した doc_update_review_v1 JSON への参照。

同時に、Sho は最初のメモ id = ..._ayatosho_001 の status を "done" に更新してもよいし、  
初期フェーズは「request は open のまま」「result は result メモで表現」で済ませてもよい。

---

## 5. 誰が「黒板に書くか」「黒板を読むか」

v1 では、役割ごとに以下を前提とする。

### 5.1 書く側（from）

- Aya  
  書くメモ:
  - to: Sho, kind: "doc_update_review_request"  
    → 自分の doc_update_proposal_v1 をレビューしてもらいたいとき。

- Sho  
  書くメモ:
  - to: Aya, kind: "doc_update_review_result"  
    → レビュー結果を通知するとき。
  - 将来: to: Tsugu, kind: "doc_update_apply_request" など。

- Hana / Kai / Haku / Tsugu  
  v1 ではまだ具体的なメモタイプは定義しないが、将来 kind を追加する余地を残す。

### 5.2 読む側（to）

- Sho  
  黒板から取得すべきメモ:
  - to == "Sho" かつ kind == "doc_update_review_request" かつ status == "open"

  読み方のタイミング:
  - v1 では、Actions の "Doc Update Review (Sho)" Workflow 実行時に黒板を読み、  
    未処理のメモがあれば 1 件ずつ処理する。

- Aya  
  黒板から取得すべきメモ:
  - to == "Aya" かつ kind == "doc_update_review_result"（自分の proposal に対する結果）

- Tsugu / Haku / Kai / Hana  
  v1 では「読むべきメモ」はまだ定義しない。  
  将来、Apply や Metrics のフロー設計時に追加で決める。

※ 詳細ルーティング（誰がどの kind を書けるか／読めるか）は、  
将来的に docs/pm/roles_routing_v1.md のような別ドキュメントで整理する。

---

## 6. トリガーとブラックボード

### 6.1 人間トリガー（Actions UI）

- v1 の前提は、「各人格の Workflow は GitHub Actions の Run workflow を啓が押す」こと。
- 例: Sho（Doc Update Reviewer）:
  - Actions UI から "Doc Update Review (Sho)" を選択し、「Run workflow」。
  - Workflow 実行中に黒板を読み、to: "Sho" のメモを処理する。

### 6.2 定期バッチ / 自動トリガー（将来）

- 将来的には、以下のようなトリガーも検討余地がある：
  - cron による定期チェック（例: Haku が日次で黒板を走査）
  - workflow_run による連鎖（例: Aya の Doc Update Proposal 完了 → 自動で Sho をキック）

ただし、現フェーズでは「人間トリガー＋黒板」というシンプルな形を維持する方針とする。

---

## 7. 今後の TODO（v1 から v2 に向けて）

- reports/board/doc_update_board_v1.jsonl（黒板ファイル）の実装案を、コード／Workflow に落とす。
- Sho v1 Workflow から、
  - proposal_path を直接指定する方式と、
  - 黒板を読んで「open なメモを処理する」方式のどちらから始めるかを決める。
- roles_v1 と黒板の関係（誰がどの kind を書けるか／読むか）を  
  roles_routing_v1 的なドキュメントとして整理する。

本ドキュメントは blackboard_v1_draft として保持し、  
実装と運用の知見を踏まえて blackboard_v1 に昇格させる。
