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

## 5. 標準質問（Standard Prompt）

PM Kai v1 を呼び出すときの標準的な要求は、次のとおりとする。

- 対象プロジェクト: `<project_id>`
- 入力コンテキスト:
  - `docs/projects/<project_id>/project_definition.md`
  - `STATE/<project_id>/current_state.md`
  - `reports/<project_id>/直近の *_weekly.md`（最新の1つ）
  - 必要に応じて、直近の Issue / PR の要約
- 出力要件:
  1. pm_snapshot_v1 JSON
  2. 1 行だけ `---`
  3. JSON の内容を要約した Markdown ビュー

人間向けの質問文の例:

対象プロジェクト `<project_id>` について、次のファイルと直近の Issue / PR を前提に、pm_snapshot_v1 の JSON と、その内容を要約した Markdown ビューを出してください。

参照してよいファイル:
- `docs/projects/<project_id>/project_definition.md`
- `STATE/<project_id>/current_state.md`
- `reports/<project_id>/直近の *_weekly.md`（最新の1つ）

必ず以下を含めてください。
- C（Current）
- G（Goals: short_term / mid_term）
- δ（Gaps）
- Next 3（next_actions: 3 件）
- Evidence（どのファイル/Issue/PR を根拠にしたか）

出力フォーマット:
1) まず pm_snapshot_v1 JSON を出力する  
2) その直後の行に `---` を 1 行だけ出力する  
3) 続けて人間向けの Markdown ビューを出力する
