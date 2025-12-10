# info_source_bundle_v1（情報の束フォーマット）

## 目的

PM Kai / Aya が扱う「情報の束」の標準フォーマットを定義する。

- project_id ごとの様々な情報源（current_state, weekly, memo, issue コメントなど）を、最終的には同じ入口フォーマットで渡せるようにする。
- 生のテキストは raw_text にそのまま入れ、不定形で構わない。
- そのうえで最低限のメタ情報（source_type や hints）を付けることで、Kai / Aya が info_node_v1 / info_relation_v1 を切り出しやすくする。

## スキーマ（イメージ）

YAML 例:

```yaml
info_source_bundle_v1:
  project_id: "hakone-e2"
  source_type: "weekly"        # 例: "state_doc" | "weekly" | "memo" | "issue_comment" | "meeting_note"
  source_id: "2025-12-14_weekly"
  title: "Hakone-e2 weekly 2025-12-14"
  time_range:
    from: "2025-12-08"
    to: "2025-12-14"
  raw_text: |
    ここに不定形テキストがそのまま入る。
    Markdown でも、ただの文章でも良い。
  hints:
    - "C/G/δ に対応しそうなポイントを意識してノードを作ってください。"
    - "新しいタスクがあれば task ノードにし、関連する Gap/Goal に紐づけてください。"
  tags:
    - "week:2025-12-14"
    - "kind:weekly"
```

## 必須フィールド

- project_id: string  
  - 例: "vpm-mini", "hakone-e2"
- source_type: string  
  - 情報源の種類。初期値の想定:
    - "state_doc"（STATE/**/current_state.md 相当）
    - "weekly"
    - "memo"
    - "issue_comment"
    - "meeting_note"
- source_id: string  
  - 情報源を一意に識別する ID。例: "2025-12-14_weekly", "issue-571-comment-1"
- raw_text: string  
  - 情報本体。不定形テキストそのもの。Markdown を含んでも良い。

## 推奨フィールド

- title: string  
  - 人間向けのタイトル。
- time_range: { from: string, to: string }  
  - この情報が主にカバーする期間。
- hints: string[]  
  - Kai / Aya へのヒントとなる指示文。自然言語でよい。
- tags: string[]  
  - 後から検索・フィルタリングしたいときのラベル。

## 使用方針

- current_state.md や weekly, memo など、どのような情報源であっても、最終的には info_source_bundle_v1 に包んでから Kai / Aya の変換器に渡す。
- project_id と source_type / source_id の組み合わせにより、後で trace できるようにする。
- bundle の出力先は info_node_v1 / info_relation_v1 を含む JSON（info_snapshot の "素材"）とする。
