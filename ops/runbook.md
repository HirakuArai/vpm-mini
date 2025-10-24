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

Artifacts: `artifacts/out.png`, `artifacts/evidence.log`, `artifacts/headers.txt`, and `artifacts/png_head.hex`. Evidence lines now include `HTTP`, `CT`, `UID`, `panelId`, `from`, `to`, `size`, and `HEADHEX` (first 16 bytes as hex). Success requires `== FOOTER == OK` on the last line.

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

Render success criteria (all must hold):
- `HTTP=200`
- `CT=image/png`
- `HEADHEX` starts with `89 50 4e 47` (PNG signature)
- `size` ≥ `MIN_PNG_BYTES` (default 512B, overridable via env)
- Footer `== FOOTER == OK`

On failure, inspect:
- `artifacts/evidence.log` — confirm HTTP/CT/size/signature
- `artifacts/headers.txt` — raw HTTP headers from Grafana
- `artifacts/png_head.hex` — first 16 bytes of the PNG payload

If `HTTP=302` or `CT=text/html` the Grafana token/org is invalid; diagnose via the `Grafana Diagnostics` workflow (checks `/api/health` with/without token).

## Token guard

Token Guard remains mandatory; PRs fail if `/user` or `/actions/workflows` are unreachable.
