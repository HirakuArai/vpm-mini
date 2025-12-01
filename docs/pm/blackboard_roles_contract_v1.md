Blackboard Roles Contract v1

（Doc Update レーン向けロール契約）

1. 目的とスコープ

本ドキュメントは、docs/pm/blackboard_core_spec_v1.md で定義された
黒板 (blackboard) entry のコア仕様の上に、

誰が（どのロールが）

どの entry を「自分の仕事」とみなし（pick し）

処理後にどのような entry を書くか（write するか）

を整理したロール別の契約 (roles contract) を定義する。

v1 の適用範囲は、まず Doc Update レーンに限定する。

僕ら（Human） → Aya → Sho → Tsugu → Gen → 僕ら（Human）


という 1 巡（ぐるり）の中で、黒板 entry をどのようにやり取りするかを
明確にすることを目的とする。

その他のレーン（例: metrics-echo、hakone-e2 など）への適用は、
本 contract をベースに将来拡張する。

2. 共通ルール
2.1 対象フィールド

黒板 entry のフィールド構造は、
docs/pm/blackboard_core_spec_v1.md に従う。

本ドキュメントでは、特に次のフィールドを前提にする。

id: string

from: string

to: string

project_id: string

kind: string

status: string

payload: object

target_docs: array

created_at: string

updated_at: string

および、必要に応じて:

source_issue, source_comment_id, source_run_id, note

2.2 pick 条件（「自分の仕事」とみなす条件）

ロール X が黒板 entry を読むとき、
その entry を「自分の仕事」とみなす基本条件は以下とする。

to が自分のロール名である

status が "open" である

project_id が "vpm-mini" である

kind がそのロールの allowed_kinds に含まれている

これらをすべて満たす場合にだけ、
ロールは entry を「自分の仕事」として処理する。

2.3 kind と payload の扱い

kind は、「処理の種類」を表す識別子。

payload は、「処理内容」を表すオブジェクト。

v1 の Doc Update レーンでは、次の kind 群を扱う。

"doc_update_proposal_request"
（Human → Aya）

"doc_update_review_request"
（Aya → Sho）

"doc_update_apply_request"
（Sho → Tsugu）

"doc_update_error"
（エラー通知用、宛先は主に Human または Hana を想定）

payload の詳細なスキーマは、各 kind ごとの spec（将来の doc）で扱う。
本ドキュメントでは「どのロールがどの kind を扱うか」にフォーカスする。

2.4 status の基本ポリシー

最低限のルール:

Human が「仕事を依頼するとき」は status を "open" で entry を作成する。

ロールが「自分に割り当てられた仕事を完了した」ときは、

既存 entry の status を "done" に更新する、
または

新たに "done" 状態相当の entry を作成する（v1 では前者を優先）。

処理中状態（"in_progress"）は v1 では必須ではないが、
将来追加してもよい。

エラー時は、可能であれば status が "error" の entry を Human または Hana 宛てに出す。

3. ロール別契約
3.1 Human（僕ら）
3.1.1 役割の位置づけ

Doc Update レーンの起点と終点。

「現実の変化の意図」を黒板に書き込み、

最後に Gen の pm_snapshot を読んで「そうそう、今こうなっているはず」と確認する。

3.1.2 読む entry

Human は、形式的な pick ルールには縛られないが、
v1 では主に次のような entry に関心を持つ。

to が "Human" で status が "open" または "error" または "done" の黒板 entry

特に kind が "doc_update_error" の entry は優先的に確認対象。

3.1.3 書く entry（Doc Update レーン起点）

Doc Update レーンを始動するとき、Human は Aya 宛てに
"doc_update_proposal_request" entry を作成する。

サンプル:

{
  "id": "vpm-mini-docupdate-issue571-1",
  "from": "Human",
  "to": "Aya",
  "project_id": "vpm-mini",
  "kind": "doc_update_proposal_request",
  "status": "open",
  "payload": {
    "summary": "STATE/current_state と pm_snapshot_spec を今の運用に合わせて整えたい",
    "details": {
      "reason": "Gen の pm_snapshot が「今の Kai の役割」を自然に表現できるようにするため",
      "hints": [
        "STATE/current_state.md の C/G/δ を最新の Phase に合わせたい",
        "docs/pm/pm_snapshot_v1_spec.md の as_of_date ポリシーを明文化したい"
      ]
    },
    "refs": {
      "source_issue": 571
    }
  },
  "target_docs": [
    "STATE/current_state.md",
    "docs/pm/pm_snapshot_v1_spec.md"
  ],
  "created_at": "2025-11-30T02:30:00+09:00",
  "updated_at": "2025-11-30T02:30:00+09:00"
}

3.1.4 status 更新

v1 では、Human は通常、自分が作成した entry の status を手動でいじらない。

レーン完了後に、必要であれば "canceled" にするなどの運用は将来検討。

3.2 Aya
3.2.1 役割

Doc Update レーンにおける提案生成役。

Human からの意図（黒板 entry）と SSOT（STATE / docs / pm_snapshot）を読み、
doc_update_proposal_v1.json を生成する。

3.2.2 allowed_kinds と pick 条件

Aya が「自分の仕事」として拾う entry:

to が "Aya"

status が "open"

project_id が "vpm-mini"

kind が "doc_update_proposal_request"

allowed_kinds（v1）:

{"doc_update_proposal_request"}

3.2.3 出力（書くもの）

Aya は黒板 entry そのものを更新するのではなく、
主に次を出力する。

reports/doc_update_proposals/.../doc_update_proposal_v1.json
（既存の Aya レーン仕様に準拠）

黒板への直接の書き込みは v1 では必須ではない。
ただし、将来「Aya から Sho 宛ての blackboard entry を起こす」運用に移行する可能性があるため、
その場合の想定をメモしておく。

Aya → Sho 宛ての "doc_update_review_request" entry の例:

{
  "id": "vpm-mini-docupdate-review-issue571-1",
  "from": "Aya",
  "to": "Sho",
  "project_id": "vpm-mini",
  "kind": "doc_update_review_request",
  "status": "open",
  "payload": {
    "summary": "Aya による doc_update_proposal_v1 のレビュー依頼",
    "details": {
      "proposal_path": "reports/doc_update_proposals/2025-11-30-vpm-mini.json"
    },
    "refs": {
      "source_issue": 571
    }
  },
  "target_docs": [
    "STATE/current_state.md",
    "docs/pm/pm_snapshot_v1_spec.md"
  ],
  "created_at": "...",
  "updated_at": "..."
}


v1 の実装状況に合わせて、「Aya が黒板に書くかどうか」は段階的に導入してよい。

#### Implementation note (v1 現状)

- Aya は Human → Aya のエントリから、`to` / `status` / `project_id` / `kind` に加え、`payload_ref.value`（進捗サマリーのパス）を利用する。  
- 現時点では core spec の `payload` / `target_docs` / `updated_at` などは pick ロジックで検証していない。  
- Doc Update v1 に合わせる場合は、Human → Aya エントリに `payload_ref.value` を含めることが実装上の前提となる。将来的に `payload` や `target_docs` の利用・検証を強化し、core spec に近づける余地がある。

3.2.4 エラー時の扱い（方針）

必須フィールド欠落などで entry を解釈できない場合は、

workflow 側のログにエラーを出す。

黒板 entry にはまだ触らない（v1 では error entry すら書かない方針でもよい）。

将来、"doc_update_error" entry を Human または Hana 宛てに書く運用にすることを検討する。

3.3 Sho
3.3.1 役割

Doc Update Review 担当。

Aya の proposal と現行ファイルを読み、
各 target_file ごとの差し替え後全文 (final_content) を確定する。

3.3.2 allowed_kinds と pick 条件

Sho が「自分の仕事」として拾う entry のターゲット像:

to が "Sho"

status が "open"

project_id が "vpm-mini"

kind が "doc_update_review_request"

allowed_kinds（v1 想定）:

{"doc_update_review_request"}

現状の実装では、Sho は

doc_update_proposal_v1.json のパスを workflow 引数でもらい、

そこから直接 proposal を読む

構成になっているため、黒板との結合は次のステップで行う。

3.3.3 出力

doc_update_review_v1.json を生成し、
各 target_file ごとに final_content を含む。

change_type = "replace_whole_file" を前提にしている。

黒板への書き込みは v1 では必須ではないが、将来的には:

Sho → Tsugu 宛ての "doc_update_apply_request" entry を作成し、

payload.details.review_path で doc_update_review_v1.json を指す

という形にすることを想定している。

3.4 Tsugu
3.4.1 役割

doc_update_apply_v1 apply マシン。

Sho の review JSON を読み、条件を満たす場合にだけ
final_content を既存ファイルに当てて PR を作成する。

3.4.2 allowed_kinds と pick 条件

将来の黒板連携のターゲットとして:

Tsugu が「自分の仕事」として拾う entry:

to が "Tsugu"

status が "open"

project_id が "vpm-mini"

kind が "doc_update_apply_request"

allowed_kinds（v1 想定）:

{"doc_update_apply_request"}

現時点では、Tsugu は

GitHub Actions の workflow 引数で review_json_path を受け取る

構成のため、黒板連携は次のフェーズで導入する。

3.4.3 出力（成功時）

Tsugu は apply に成功した場合、次を行う。

feature/doc-update-apply-<review_run_id> ブランチを作成し、

final_content でファイルを更新し、

evidence ラベル付きの PR を作成し、

CI (evidence_dod など) が成功する状態にする。

黒板側の contract（成功時）としては、

対応する起点 entry（例: "doc_update_apply_request"）の status を "done" に更新する
もしくは

別の entry（例: kind が "doc_update_apply_request_result"）で status = "done" を表現する

という形を v1 のターゲットとする。

3.4.4 出力（エラー時）

エラー時の推奨案（まだ実装必須ではない）。

to が "Human" または "Hana"

kind が "doc_update_error"

status が "open"

の entry を作成し、payload.details にエラー内容を記録する。

3.5 Gen
3.5.1 役割

PM Snapshot v1 の実行主体。

as_of_date をキーとした 1 日スナップショットとして、
C/G/δ/Next を STATE/weekly 等に書き出す。

3.5.2 黒板との関係（v1）

v1 では、Gen は黒板 entry を直接 read/write しない。

Doc Update レーンを通じて更新された

STATE/current_state.md

各種 docs/pm/*.md

の内容をもとに、pm_snapshot を生成する。

将来的な方向性としては:

open と done の Doc Update エントリ一覧を
C/G/δ/Next の補助情報として扱う可能性はあるが、

本 contract v1 では範囲外とする。

4. Doc Update レーンの「ぐるり一周」例

ここでは、黒板を使った Doc Update レーンが
僕ら → Aya → Sho → Tsugu → Gen → 僕ら の順で 1 巡するイメージをまとめる。

僕ら（Human）

「プロジェクトのこういう情報を揃えたい」という意図を整理し、

Aya 宛てに doc_update_proposal_request entry（status = "open"）を黒板に書く。

Aya

黒板 entry（Human → Aya）と SSOT（STATE / docs / pm_snapshot）を読み、

doc_update_proposal_v1.json を生成する。

将来、Sho 宛てに doc_update_review_request entry を書く可能性がある。

Sho

Aya の proposal と現行ファイルを読み、

doc_update_review_v1.json を生成し、各ファイルの final_content を確定する。

将来、Tsugu 宛てに doc_update_apply_request entry を書く可能性がある。

Tsugu

review JSON を読み、

条件（risk = low、review_mode = auto_accept_v1、target_files が STATE と docs のみ）を満たすものについて
final_content を当てて PR を作成する。

CI が成功し、PR がマージされる。

将来、対応 entry の status を "done" に更新する。

Gen

更新後の STATE と docs をもとに pm_snapshot を実行し、

as_of_date ごとの C/G/δ/Next を出力する。

僕ら（Human）

Gen の pm_snapshot を読み、

「このプロジェクトは何で、今どういう状態で、どこを目指しているか」が
自分の意図どおりに反映されているかを確認する。

この「ぐるり一周」が破綻なく通ることが、
Doc Update レーン v1 のゴールイメージである。

5. 今後の拡張メモ

Aya / Sho / Tsugu が黒板 entry を read/write するステップは、
v1 実装の進み具合に応じて段階的に導入する。

kind ごとの payload schema（例: doc_update_proposal_request の payload.details 構造）は、
将来的に別 spec に切り出す。

Gen が黒板の open/done 状況を取り込んで
C/G/δ/Next の精度を高めるリファインメントは v2 以降の検討事項とする。
