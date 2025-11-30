# Tsugu PR CI findings (inspect_ci_for_tsugu_pr_v1 prep)

Context: Tsugu apply PRs (author=github-actions, head_ref=feature/doc-update-apply-*) show Required checks (evidence-dod, healthcheck, k8s-validate, knative-ready, test-and-artifacts) as “Expected — Waiting for status to be reported”. Investigation of `.github/workflows` without changing CI yet.

## Mapping of required checks to workflows/jobs
- evidence-dod → `.github/workflows/evidence_pr_checks.yml` job `evidence-dod` (also echoed in `_ask_pr_checks.yml`, `ask_pr_checks.yml`, `pr_validate.yml` aliasing, but required check points to evidence_pr_checks version).
- healthcheck → `evidence_pr_checks.yml` job `healthcheck` (standalone `healthcheck.yml` mirrors it).
- k8s-validate → `evidence_pr_checks.yml` job `k8s-validate` (heavier `pr_validate.yml` has same name but required check likely bound to evidence version).
- knative-ready → `evidence_pr_checks.yml` job `knative-ready` (full version in `pr_validate.yml`).
- test-and-artifacts → `evidence_pr_checks.yml` job `test-and-artifacts` (standalone `test-and-artifacts.yml` exists with same name).

## Why Tsugu PRs are skipped
- All jobs in `evidence_pr_checks.yml` (and the standalone `healthcheck.yml` / `test-and-artifacts.yml`) have `if: contains(github.event.pull_request.labels.*.name, 'evidence')`.
- Tsugu apply PRs created by github-actions do not carry the `evidence` label, so every required check is skipped → status stays “Expected”.
- No branch/path filters block docs/STATE changes; the gating condition is the missing `evidence` label. Author/head_ref are not explicitly excluded.

## Recommendations (not applied yet)
- Easiest: ensure Tsugu apply PRs get label `evidence` on creation (in apply workflow after `gh pr create`, or via a small labeler workflow keyed on head_ref `feature/doc-update-apply-*`).
- Alternative: relax `if` conditions to run when label is absent but PR head matches `feature/doc-update-apply-*` or author is `github-actions`.
- Consider consolidating required checks to a single source (either evidence_pr_checks or pr_validate) to avoid ambiguity between similarly named jobs.
- Verify branch protection required-check names exactly match the jobs you intend (currently evidence_pr_checks versions). Update branch protection if switching to pr_validate jobs.
