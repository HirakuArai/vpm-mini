# Kai-0 I/O Spec v1 (Lane Status & What Changed)

- context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Layer B cycle-1 / Kai-0 design)
- Scope: Layer B / doc_update lane only. Kai-0 is a hands-on assistant, not a command tower.
- Goal: Make Kai-0 responses understandable to humans and machines, with structured JSON plus concise Markdown summaries.

## 1. Overview
- Role: Kai-0 answers prompts from ChatGPT or humans with lane status or recent changes, returning a structured payload and a short summary.
- Audience: PMs and workflows needing consistent machine-readable outputs for the doc_update lane.
- Boundaries: No orchestration duties; strictly reporting and summarizing for vpm-mini Layer B / doc_update.

## 2. Input: `kai_request_v1` (ChatGPT → Kai)
- Purpose: Normalize questions sent by ChatGPT, humans, or workflows into a single JSON envelope.
- Fields:
  - `version`: fixed `"kai_request_v1"`.
  - `request_id`: unique ID (timestamp or UUID).
  - `from.actor_type`: `"chatgpt"` | `"human"` | `"workflow"`.
  - `from.actor_id`: optional identifier (model name, user, workflow name).
  - `project_id`: fixed to `"vpm-mini"` for v1.
  - `type`: `"lane_status"` | `"what_changed"`.
  - `lane.layer`: fixed `"layer_b"` for v1.
  - `lane.name`: fixed `"doc_update"` for v1.
  - `params.time_window_days`: days for `what_changed`; default `7`.
  - `params.max_highlights`: highlight cap; default `5`.
- Example:
```json
{
  "version": "kai_request_v1",
  "request_id": "req-2024-10-05T12:00:00Z",
  "from": { "actor_type": "chatgpt", "actor_id": "gpt-4o" },
  "project_id": "vpm-mini",
  "type": "lane_status",
  "lane": { "layer": "layer_b", "name": "doc_update" },
  "params": { "time_window_days": 7, "max_highlights": 5 }
}
```

## 3. Output: `kai_response_v1` (Kai → ChatGPT)
- Purpose: Pair a structured payload with a short human-readable summary.
- Fields:
  - `version`: fixed `"kai_response_v1"`.
  - `request_id`: echoes the incoming `request_id`.
  - `status`: `"ok"` | `"error"`.
  - `meta.generated_at`: ISO8601 timestamp.
  - `meta.kai_version`: Kai-0 internal version (e.g., `"0.1.0"`).
  - `payload.kind`: `"lane_status_v1"` | `"what_changed_v1"`.
  - `payload.data`: body defined in Sections 4–5.
  - `summary_md`: 3–5 line Markdown digest (heading + bullets recommended).
  - `notes`: array of supplemental notes (evidence references, next steps, caveats).
- Example (lane status):
```json
{
  "version": "kai_response_v1",
  "request_id": "req-2024-10-05T12:00:00Z",
  "status": "ok",
  "meta": { "generated_at": "2024-10-05T12:00:02Z", "kai_version": "0.1.0" },
  "payload": {
    "kind": "lane_status_v1",
    "data": { "...": "see Section 4" }
  },
  "summary_md": "## Layer B / doc_update status\n- Cycle-1 completed; latest artifact: doc_update_review_v1.json\n- No blockers reported",
  "notes": ["Evidence: issue #841; artifacts under reports/doc_update_proposals/"]
}
```

## 4. Payload `lane_status_v1`
- Purpose: Report the current position and cycle state for Layer B / doc_update.
- Expected evidence sources: issue `#841 [board] doc_update_blackboard_v1`, Aya artifact `doc_update_proposal_v1.json`, Sho artifact `doc_update_review_v1.json`, Apply/Tsugu PRs (e.g., `#847`, `#849`), `STATE/vpm-mini/current_state.md` Layer B section.
- Structure (described, Kai generates JSON):
  - `kind`: `"lane_status_v1"`.
  - `project_id`: `"vpm-mini"`.
  - `lane`: `{ "layer": "layer_b", "name": "doc_update" }`.
  - `as_of`: timestamp representing the status cutoff.
  - `cycle`:
    - `latest_cycle_id`: e.g., `"cycle-1"`.
    - `status`: `"completed"` | `"in_progress"` | `"blocked"`.
    - `started_at`, `completed_at`: timestamps.
  - `steps`: entries for `aya`, `sho`, `tsugu` (and others if added):
    - `status`: `"completed"` | `"in_progress"` | `"skipped"` | `"error"` etc.
    - `latest_entry`:
      - `blackboard_issue`: numeric (typically `841`).
      - `blackboard_comment_id`: related comment ID.
      - `actions_workflow`: executed workflow name.
      - `actions_run_id`: Actions run ID.
      - `artifact_path`: main JSON artifact path (e.g., `reports/doc_update_proposals/...`).
      - `updated_at`: last update timestamp.
      - `summary`: 1–2 sentence description.
  - `state_view`:
    - `state_file`: `STATE/vpm-mini/current_state.md`.
    - `section_anchor`: anchor to Layer B section (e.g., `#layer-b-doc-update-v1`).
    - `digest`: one-line snapshot of Layer B state.
    - `known_gaps`: list of missing pieces or bottlenecks.
  - `next_suggested_actions`: array of candidate actions (`id`, `title`, `owner`, `priority`, etc.) Kai deems useful next.

## 5. Payload `what_changed_v1`
- Purpose: Summarize what happened in vpm-mini over the last N days with highlights.
- Expected evidence sources: recent PRs/issues/Actions runs, doc_update workflows added/changed, updates in `STATE` / `docs` / `reports`.
- Structure (described, Kai generates JSON):
  - `kind`: `"what_changed_v1"`.
  - `project_id`: `"vpm-mini"`.
  - `time_window`: `{ "from": "YYYY-MM-DD", "to": "YYYY-MM-DD" }`.
  - `highlights`: ordered list of key events:
    - `rank`: `1`, `2`, `3`, ...
    - `category`: e.g., `"layer_b"`, `"workflow"`, `"state_doc"`.
    - `title`: short headline.
    - `summary`: 2–3 sentence overview.
    - `evidence`: links to issues/PRs/state files/docs (`type`, `id`, `title`, `path`, `url`, etc.).
  - `by_category`:
    - `workflows`: run counts and latest status per relevant workflow.
    - `prs`: list of high-impact PRs (number, title, status, impact).
    - `state_docs`: notable changes to `STATE` or `docs`.
  - `risks`: anticipated risks or unreflected items (e.g., PM Snapshot not yet reflecting Layer B cycle-1).
  - `open_questions`: unresolved points Kai perceives.

## 6. Operational Notes (Kai-0)
- Avoid heredoc-based raw JSON generation inside YAML (implementation guideline).
- Use `gh run download` to fetch artifacts.
- Do not modify `STATE/current_state.md` in parallel within the same section.
- For apply/workflow changes, always branch from `main` (no branch reuse).
- Extract and condense long Codex prompts into a spec like this rather than embedding prompts verbatim.
