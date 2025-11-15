/ask pr_groomer_suggest 仕様メモ（M-2）

目的と位置づけ

フェーズ:

開発フェーズ: Phase 2 後半（Runner + /ask / Goal-M2）

記憶フェーズ: M-2（ルール運用 → 半自動化）

ゴール:

開いている PR を、状態と役割に基づいて整理するための「提案エンジン」として /ask を使う。

具体的には、PR を以下のようなカテゴリに分類する案を出させる:

ssot: SSOT 本流に関わる PR（コード / インフラ / STATE / docs / data など）

ephemeral: 一時的な実験・証跡専用の PR（役目を終えたら Close 候補）

needs-triage: まだ方向性が決まっていない / 途中で止まっている PR

blocked: 外部依存や権限待ちなどで進められない PR

この段階では、/ask は「PR ごとのカテゴリ＋推奨アクション案」を出すだけで、実際に Close するかどうかは人間が判断する。

インターフェース（/ask の呼び方）

GitHub Issue / PR コメントの 1 行目:

/ask pr_groomer_suggest


2 行目以降に、AI に渡すコンテキストを貼る:

開いている（または対象としたい）PR の一覧を JSON 形式（CONTEXT_JSON）で貼る。

CONTEXT_JSON は、gh pr list --json ... の結果を人間が整形したものを想定する。

例:

/ask pr_groomer_suggest
下記 CONTEXT_JSON をもとに、各 PR のカテゴリと推奨アクション案を返してください。

CONTEXT_JSON:
{ ... }


3. 入力フォーマット（CONTEXT_JSON）

3.1 フィールド構成（暫定）

CONTEXT_JSON は、最低限以下の形を想定する。

{
  "pull_requests": [
    {
      "number": 728,
      "title": "Docs: /ask update_north_star spec (M2-1)",
      "state": "open",
      "draft": false,
      "labels": ["docs", "memory"],
      "head_ref": "feat/update-north-star-spec",
      "base_ref": "main",
      "author": "HirakuArai",
      "created_at": "2025-11-15T20:40:00Z",
      "updated_at": "2025-11-15T20:47:00Z",
      "has_conflicts": false,
      "is_experiment_hint": false,
      "notes_from_human": "M2-1 の spec 追加。マージ待ち。"
    }
  ]
}


フィールドの意味（暫定）:

number: PR 番号（必須）

title: PR タイトル（必須）

state: open / closed / merged など（基本 open を対象とする）

draft: Draft PR かどうか

labels: string 配列（ssot, docs, experiment, evidence, runner など）

head_ref: ブランチ名（例: feat/update-north-star-spec）

base_ref: 対象ブランチ（例: main）

author: 作成者の GitHub login

created_at / updated_at: ISO8601 文字列（古い PR を判断する参考）

has_conflicts: true の場合、コンフリクトがあることを示すヒント

is_experiment_hint: 人間が「これは実験系かもしれない」と思う場合に true にしてよい

notes_from_human: 補足コメントがあれば自由記述

必須フィールド（暫定）:

number

title

state

labels

head_ref

CONTEXT_JSON 自体は、M-2 段階では人間が作る前提とする。
将来的に、gh pr list から自動生成するスクリプトを追加してもよい。

出力フォーマット（AI が返すべき形）

AI は、必ず以下の JSON だけを返す（説明テキストは rationale に埋め込む）。

{
  "classifications": [
    {
      "number": 728,
      "category": "ssot",
      "recommended_action": "merge_when_green",
      "reason": "M2-1 の spec 追加で、docs/memory/** に対する SSOT ドキュメント拡張。ラベルも docs/memory 系で揃っているため ssot 扱いが妥当。"
    }
  ],
  "rationale": [
    "labels, head_ref 名、タイトル、notes_from_human から、PR の目的と役割を推定してカテゴリを決める。",
    "明らかに実験ログや一時 evidence のみを含む PR は ephemeral 候補とする。",
    "古くて更新が止まっている PR は needs-triage として人間に再判断を促す。"
  ],
  "warnings": [
    "人間が is_experiment_hint を true にしている PR は、category を ephemeral にする前提でよいか確認してください。",
    "blocked カテゴリに分類された PR は、notes_from_human にブロック要因を追記してから扱ってください。"
  ]
}


4.1 category の値と意味

ssot:

SSOT 本流（コード / インフラ / STATE / docs / data など）に関わる PR。

原則として「merge を目指す」対象。

ephemeral:

一時的な実験・ログ・証跡のための PR。

役目を終えたら Close 候補。

needs-triage:

方針がまだ固まっていない / 中途半端な状態で止まっている PR。

ラベルや notes_from_human を整えた上で、ssot / ephemeral / blocked のどれにするか再判断が必要。

blocked:

外部依存（権限、他チーム、インフラ待ちなど）で進められない PR。

notes_from_human にブロック要因を書いておくことを推奨。

4.2 recommended_action の値（例）

keep_open: 今は開いたままでよい（情報として残す）。

close: 終了して良いので Close 候補。

merge_when_green: CI が通ればマージを検討。

needs_decision: 人間で方針を決める必要がある。

clarify_scope: タイトル・ラベル・説明を整理することを推奨。

DoD（M2-2 としての完了条件）

docs/memory/pr_groomer_spec.md が main ブランチに追加されている。

このファイルは、/ask 実行時に参照される仕様として自己完結している。

対応 PR の説明文に、

Phase M-2 の一環として、

/ask pr_groomer_suggest による PR グルーミング仕様を追加したこと
が記載されている。
