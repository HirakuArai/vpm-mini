# Incident: workflow_dispatch 422 with enable=204

- Repo: HirakuArai/vpm-mini
- Affected WFs & IDs: render_grafana_png_v2 (199751410), render_grafana_png_v3 (199756188), render_manual (199776648)
- Symptom: enabling the workflow succeeds (`204`), but `workflow_dispatch` requests return `422` and the Actions UI omits the "Run workflow" button. Listing via `/actions/workflows` succeeds and other workflows accept dispatches.
- Token: fine-grained PAT with repository / Actions scopes; `/user` returns `200`.
- Workaround: manual execution via branch push (`render_on_push.yml`) and daily cron wrapper calling the reusable workflow.
- Status: reusable workflow captured as minimal repro; awaiting GitHub fix before re-introducing manual dispatch on render workflows.
