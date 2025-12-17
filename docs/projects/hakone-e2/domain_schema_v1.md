# Hakone Ekiden Domain SSOT (A方式) — schema v1

このドキュメントは「箱根駅伝の事実情報（事実+根拠+解釈）」を保存する A方式（Domain SSOT）の最小スキーマを定義する。
B方式（hakone-e2 Project黒板: data/hakone-e2/info_*）は設計/運用/タスクのみであり、個別事実レコード・解釈データは置かない。

## 物理配置（A方式SSOT）
- data/hakone-e2/domain/e2_entities_v1.json
- data/hakone-e2/domain/e2_events_v1.json
- data/hakone-e2/domain/e2_evidence_v1.json
- data/hakone-e2/domain/e2_claims_v1.json
- data/hakone-e2/domain/e2_hypotheses_v1.json
- data/hakone-e2/domain/e2_scenes_v1.json

## 基本原則
- 断定（claim）は必ず evidence_refs を持つ（推測禁止）
- 解釈（hypothesis）も evidence_refs を持てる（“根拠のある解釈”を許容）
- 事実（claim）と解釈（hypothesis）は分離する
- 各itemは meta を optional で持ち、来歴（schema_version/run_id/timestamps）を A側だけで完結させる

## 最低Quality Gate（更新時に必ず守る）
- claim.evidence_refs が空のレコードは追加しない
- refs（entity/event/evidence/claim/hypothesis/scene）が参照切れしない
- claim.key の重複は「同一断定の重複」なので検知する（運用で上書き/統合を決める）
