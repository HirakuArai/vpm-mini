# PM Kai v1 出力仕様（pm_snapshot_v1）

## 1. 目的

本仕様は、vpm-mini プロジェクトにおける PM Kai v1 の標準出力形式を定義する。

PM Kai v1 は、GitHub 上の情報（project_definition / STATE / reports / Issue / PR）を入力として受け取り、

- 現在地（C）
- ゴール（G）
- ギャップ（δ）
- 次にやるべきこと（Next 3）
- それらの根拠となる Evidence

を、一貫したフォーマットで返すことを目的とする。

将来的には project_id を切り替えることで、他プロジェクトにも同じ仕様を適用する。

## 2. JSON フォーマット（機械向け）: pm_snapshot_v1

PM Kai v1 の「一次出力」は、以下の JSON 構造とする。

例:

{
  "schema_version": "pm_snapshot_v1",
  "project_id": "vpm-mini",
  "generated_at": "2025-11-23T15:30:00+09:00",

  "current": {
    "summary": "短い文章での現状サマリ（2〜3行程度）",
    "bullets": [
      "箇条書きの現状ポイント 1",
      "箇条書きの現状ポイント 2"
    ]
  },

  "goals": {
    "short_term": [
      "短期ゴール（〜数週間）"
    ],
    "mid_term": [
      "中期ゴール（〜数ヶ月）"
    ]
  },

  "gaps": [
    "ゴールに対する主なギャップ 1",
    "ゴールに対する主なギャップ 2"
  ],

  "next_actions": [
    {
      "id": "T-XXX-1",
      "title": "タスク名",
      "details": "タスクの詳細説明",
      "evidence_refs": ["STATE/vpm-mini/current_state.md"],
      "links": ["#800"],
      "impact": "high",      // high / medium / low
      "effort": "medium",    // high / medium / low
      "status": "todo"       // todo / in_progress / done
    }
  ],

  "evidence": [
    {
      "kind": "doc",
      "path": "docs/projects/vpm-mini/project_definition.md",
      "summary": "この文書が何を示しているかの短い説明。"
    },
    {
      "kind": "state",
      "path": "STATE/vpm-mini/current_state.md",
      "summary": "現在地（C/G/δ）とアクティブタスクの概要。"
    },
    {
      "kind": "report",
      "path": "reports/vpm-mini/2025-11-23_weekly.md",
      "summary": "直近の週次レポート。今週のサマリ、Done、C/G/δ、Next3 が記録されている。"
    }
  ],

  "notes": [
    "補足・メモ。PM Kai v1 の判断方針など。"
  ]
}

## 3. Markdown ビュー（人間向け）

人間向けには、JSON の内容を次の Markdown テンプレートに整形して返す。

例:

# PM Snapshot: <project_id> (<日付YYYY-MM-DD>)

## 1. Current（C: 現在地）

- 箇条書きで 2〜3 行の現状サマリ

## 2. Goals（G: ゴール）

（短期（〜数週間））

- 箇条書き

（中期（〜数ヶ月））

- 箇条書き

## 3. Gap（δ: ギャップ）

- ギャップの箇条書き

## 4. Next 3（この1〜2週間でやるべきこと）

1. タスク名1
   - 詳細説明
   - 関連: ファイルパスや Issue/PR 番号など

2. タスク名2
   - 詳細説明
   - 関連: ...

3. タスク名3
   - 詳細説明
   - 関連: ...

## 5. Evidence（このスナップショットの根拠）

- プロジェクト定義:
  - docs/projects/<project_id>/project_definition.md
- STATE:
  - STATE/<project_id>/current_state.md
- 週次レポート:
  - reports/<project_id>/<日付>_weekly.md
- 関連 PR / Issue:
  - #800 ...
  - #801 ...
  - #802 ...
  - #803 ...

## 6. Notes（補足）

- 補足メモ

## 4. 標準質問（Standard Prompt）のイメージ

PM Kai v1 を呼び出すときの標準質問は、次のようにする。

対象プロジェクト: <project_id>
以下のファイル内容と直近の Issue/PR を踏まえて、
JSON 形式 pm_snapshot_v1 と、その内容を要約した Markdown ビューの両方を出力してください。

必ず:
- C（Current）
- G（Goals: short_term / mid_term）
- δ（Gaps）
- Next 3（next_actions）
- Evidence（参照したファイル・Issue/PR）
を含めてください。
