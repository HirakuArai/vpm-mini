# Domain Update Lane (Fact Lane) v1 — hakone-e2

目的：A(domain) SSOT を「evidence(URL) → API抽出 → Quality Gate → PR」で更新する最小レーンを作る。
B(hakone-e2黒板)は触らない。

## Inputs（workflow_dispatch）
- url: evidence のURL（まずは HTML を想定）
- evidence_id: domain内でのID
- event_id: 紐づけ先イベント（任意）
- mode: dry-run | pr

## Output
- reports/hakone-e2/runs/<run_id>/
  - extracted.json（モデル出力）
  - validated.json（スキーマ検証後）
  - conflicts.json（矛盾/重複検知）
  - patch_preview.md（domain差分の要約）

## Quality Gate（必須）
- claim は evidence_refs を必ず持つ
- refs の参照切れを出さない（entity/event/evidence）
- 同一 claim.key の value 不一致は conflict として検知し、PRは review-required とする（v1は一覧を出力）
