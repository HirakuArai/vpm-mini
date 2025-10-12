# ADR: P2-3 最初の移植対象の決定
- Goal: 本日中に KService移植の“型”を確立し、初回を READY=True（Evidence PR）で確定
- Options (from VPM):
- A) hello (Knativeサンプル stateless HTTP) を標準テンプレとして移植
- B) hello-ai (依存: OpenAI API) を移植しAI連携を先行
- C) Composeサービス群を一括移植（stateful/依存重）

## recommendation
A を採用。Phase 2 で最小リスク・短時間で READY=True を証明する。
- Evidence: .vpm/intent_input_20251013_065655.md, .vpm/intent_output_20251013_065655.md, STATE/current_state.md
- Decision: <採用案を1行で>
- Next actions: <担当/期限/DoD: READY=True + Evidence PR>
