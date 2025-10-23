# Runbook — Evidence Render

## Manual trigger (only path)
**Manual entry is `manual-render` branch push; workflow_dispatch remains disabled.**

Push an empty commit to branch `manual-render`; set optional `from`/`to` in the commit message.

```bash
git switch manual-render || git checkout -b manual-render origin/manual-render
date > ops/manual-trigger.txt
git add ops/manual-trigger.txt
git commit -m "from=now-30m to=now"
git push
```

Artifacts: `out.png` and `artifacts/evidence.log`. The evidence file appends `HTTP=<code> UID=<uid> panelId=<id> from=<from> to=<to> size=<bytes>` followed by the footer `== FOOTER == OK` on success or `== FOOTER == NG` on failure.

## Daily 07:00 JST

`render_cron.yml` calls the reusable workflow on self-hosted infrastructure and uploads `out.png` & `artifacts/evidence.log` with the footer `== FOOTER == OK`.

## Dashboard target SSOT

`infra/observability/dashboard_target.json` is the single source of Grafana identifiers:

- `org`: 1
- `uid`: `evidence-prod`
- `slug`: `evidence-e28093-prod`
- `panelId`: 1

Both manual (`manual-render` push) and daily jobs load these values through the reusable workflow.

## Failure triage

Check the final line in `artifacts/evidence.log` (`HTTP / UID / panelId / from / to / size`) to confirm status before escalating.

## Token guard

Token Guard remains mandatory; PRs fail if `/user` or `/actions/workflows` are unreachable.
