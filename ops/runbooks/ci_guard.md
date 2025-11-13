# CI Guard Runbook (Evidence Lane / Code Lane)

This runbook helps triage and fix CI blockers around the Evidence lane (light) and Code lane (heavy).

## Components
- **Labeler**: auto-apply `evidence` when only `reports/ask/**` or `codex/inbox/**` changed.
- **Auto-approve (bot)**: approves evidence-only PRs using `EVIDENCE_APPROVER_TOKEN`.
- **ask_pr_checks (compose)**: lightweight required checks for evidence-only PRs.
- **code_checks_enforcer**: fails code PRs if heavy checks are missing; skips on evidence-only.

## Quick triage
1) **PR is evidence-only?**
   - Head ref starts with `ask/store/` OR label includes `evidence` OR all paths under `reports/ask/**` / `codex/inbox/**`.
2) **Not approved?**
   - Confirm secret `EVIDENCE_APPROVER_TOKEN` exists and PAT user has write access.
3) **Required pending?**
   - Evidence: `ask_pr_checks` must be green.
   - Code: `test-and-artifacts`, `knative-ready`, `k8s-validate` must be present and green (enforcer will fail if missing).
4) **Workflow not firing?**
   - Add label `evidence` or push a tiny commit to retrigger (`synchronize`).

## Playbooks
### A. Self-approval blocked
- Symptom: auto-approve step fails immediately.
- Fix: ensure PAT secret set; re-run or nudge PR.

### B. Evidence PR stuck in pending
- Ensure label `evidence` exists (labeler should set it).
- Check `ask_pr_checks` ran; if not, re-run or push a touch commit.

### C. Code PR merged without heavy checks (should not)
- Enforcer should fail such PRs. If not, verify checks names in enforcer workflow match actual contexts.

## Verification
- Create a test PR touching only `reports/ask/` → expect label `evidence` + bot approve + compose green.
- Create a test PR touching src code → expect heavy checks run and enforcer passes only if all present.

## Notes
- Rulesets Conditions UI is currently unavailable; we emulate two lanes via workflows.
- When Conditions become available, migrate to two rulesets (Evidence/Code) with matching strategy **Any**.
