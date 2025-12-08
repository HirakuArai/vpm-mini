# hakone-e2 info_network job v1（Kai → Aya）

## 目的

project_id = hakone-e2 の STATE/hakone-e2/current_state.md を、
VPMコアの info_network（info_node_v1 / info_relation_v1）上の
「意味ベースで扱える最初のスナップショット」として登録する。

- 目安として 30 前後の info_node に分割する。
- C/G/δ・タスク・Evidence の関係がわかる最小構造を作る。
- この job は Kai（Planner）→ Aya（実行）という2段階の責務を想定するが、
  実装上は 1 回の GPT コールで kai_plan と aya_output を同時に返してよい。

## 入力

- 必須:
  - STATE/hakone-e2/current_state.md
- 参照用（あれば）:
  - docs/projects/hakone-e2/project_definition.md
  - reports/hakone-e2/**_weekly.md

## 出力

- info_node_v1 の JSON 配列（30前後）
- info_relation_v1 の JSON 配列（20本以上）

フォーマット例（Kai+Ayaの両方を含む）:

```json
{
  "kai_plan": {
    "summary": "このジョブで何をするかの要約",
    "estimated_node_count": 30,
    "node_categories": [
      {"category": "project_meta", "count": 2},
      {"category": "current", "count": 4},
      {"category": "goals", "count": 4},
      {"category": "gap", "count": 5},
      {"category": "tasks", "count": 7},
      {"category": "layerB", "count": 3},
      {"category": "evidence", "count": 5}
    ],
    "notes": "C/G/δとタスクの関係を明示することを重視する。"
  },
  "aya_output": {
    "info_nodes": [
      { /* info_node_v1 */ }
      // ... 30前後
    ],
    "info_relations": [
      { /* info_relation_v1 */ }
      // ... 20本以上
    ]
  }
}
```

PM Kai / Aya / Tsugu から見ると、最低限 aya_output.info_nodes と
aya_output.info_relations があればよい。kai_plan はログ兼説明として扱う。

## 分割ポリシー（Aya向け）

1. プロジェクトメタ（2〜3ノード）

   - hakone-e2 の目的・背景・スコープを fact/project_meta として 2〜3 ノードに切り出す。

2. C/G/δ（合計 10〜15ノード）

   - 1.1 Current の箇条書きを、意味のかたまりごとに fact/state_snapshot として 3〜5ノード。
   - 1.2 Goals（短期/中期）を、それぞれ 2〜3ノードずつ。
   - 1.3 Gap を 4〜6ノードに分割。
   - 必要なら「C/G/δ 全体の総まとめ」を 1 ノード（state_snapshot）として置く。

3. Active Tasks（6〜10ノード）

   - H2-*** 系タスクを 1タスク=1ノードの task/pm_task として登録。
   - title / summary / body に current_state の記述を落とし込む。

4. Layer B ゴール・ルール（2〜3ノード）

   - Layer B（記録・構造化ループ）のゴール・運用方針の文章を、
     norm/update_policy または guideline/pm_guideline として 2〜3 ノードにする。

5. Evidence（3〜5ノード）

   - project_definition / weekly など、current_state に列挙されている重要なリンク先を、
     fact/weekly_summary or fact/project_meta として 1リンク1ノード レベルで登録。
   - この段階では中身の要約は薄くてよい。「存在と役割」がわかる程度でよい。

## relation の付け方（Aya向け）

- C/G/δ の各ノードは、hakone-e2 全体の state_snapshot ノードに part_of を張る。
- 各 H2-*** タスクノードは:
  - 対応する Gap ノードに evidence_for または derived_from。
  - 対応する Goal ノードには refers_to。
- Layer B ゴール/ルールノードは:
  - current_state の state_snapshot ルートに belongs_to。
- Evidence ノードは:
  - project_meta / state_snapshot / task ノードに対して evidence_for を張る。

## 成功条件（Kai側のチェック観点）

- ノード数が 24〜38 の間に収まっている（目安は 30 前後）。
- C/G/δ / Tasks / LayerB / Evidence のどれも「0」ではない。
- すべての H2-*** タスクノードが、少なくとも 1 つの Gap/Goal ノードと relation で結ばれている。
- STATE/hakone-e2/current_state.md 由来であることが scope.file と source_refs に明示されている。
