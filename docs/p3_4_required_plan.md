# P3-4 Plan — understanding-guard Required化 A/B + Dry-Run

## Goals
- Required化の影響をゼロリスクで観測（まずは Dry-Run）
- Post（🧭一意コメント・warnラベル・Evidence）は維持
- Local/CI の結論一致を継続

## Candidates for Required Context (proposed)
- `understanding/guard-required`         # 将来の主判定
- `understanding/snapshot-present`       # スナップショット存在
- `understanding/goals-synced`           # goals_equal=yes

※ まずは **Dry-Run** として、上記 Context に対し **success** を付けるだけ（保護ルールは変更しない）。

## Rollout Plan
1. Dry-Run（本PR）: 任意のPRで成功ステータスを発行（非ブロッキング）
2. 観測: 7〜14日、postコメント/Evidence/ラベルに異常が出ないか確認
3. A/B 設計:
   - A案: legacy guard を Required化、postは可視化補助
   - B案: postの一部（judge step）を Required化し、legacy guardは縮退
4. Switch準備: Rulesetの `required_status_checks` に上記 Context を追加（別PRで）

## Safety
- 既存Workflowは不変
- Dry-Runは **Statuses API** で success だけ付与（失敗を作らない）
