# Runbook — Evidence Render

## Manual trigger (reliable)
Push an empty commit to branch `manual-render`; set optional `from`/`to` in the commit message.

```bash
git switch manual-render || git checkout -b manual-render origin/manual-render
date > ops/manual-trigger.txt
git add ops/manual-trigger.txt
git commit -m "from=now-30m to=now"
git push
```

Artifacts: `out.png` and `evidence.log` with footer `== FOOTER == PUSH ENTRY OK`.

## Daily 07:00 JST

`render_cron.yml` calls the reusable workflow on self-hosted infrastructure and uploads `out.png` & `evidence.log` (`== FOOTER == VALIDATE: OK`).

## Token guard

Token Guard remains mandatory; PRs fail if `/user` or `/actions/workflows` are unreachable.
