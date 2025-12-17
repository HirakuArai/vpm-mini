import argparse
import json
import re
from datetime import date
from pathlib import Path

import requests
from jsonschema import validate

# OpenAI SDK (Responses API)
from openai import OpenAI

DOMAIN_DIR = Path("data/hakone-e2/domain")
RUNS_DIR = Path("reports/hakone-e2/runs")
SCHEMA_PATH = Path("schemas/hakone-e2/domain_extract_facts_patch_v1.schema.json")


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_container(path: Path):
    d = read_json(path)
    if "items" not in d or not isinstance(d["items"], list):
        raise ValueError(f"Unexpected shape: {path}")
    return d


def upsert_by_id(items, id_key, obj):
    oid = obj.get(id_key)
    if not oid:
        raise ValueError(f"missing {id_key}")
    for i, x in enumerate(items):
        if isinstance(x, dict) and x.get(id_key) == oid:
            items[i] = obj
            return "updated"
    items.append(obj)
    return "inserted"


def strip_text(html: str) -> str:
    # Ultra-minimal cleanup for v1; keeps payload size manageable.
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html[:120_000]


def call_model_json_object(model: str, prompt: str):
    client = OpenAI()
    resp = client.responses.create(
        model=model,
        input=prompt,
        text={"format": {"type": "json_object"}},
        temperature=0,
        store=False,
    )
    out = getattr(resp, "output_text", None)
    if not out:
        # SDK shape fallback; raise so we notice and can update parser.
        out = json.dumps(resp.to_dict(), ensure_ascii=False)
        raise RuntimeError("No output_text; SDK shape changed. Please update parser.")
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--evidence-id", required=True)
    ap.add_argument("--event-id", default="__UNKNOWN__")
    ap.add_argument("--mode", choices=["dry-run", "pr"], default="dry-run")
    ap.add_argument("--model", default="gpt-4.1")
    args = ap.parse_args()

    today = date.today().isoformat()
    run_id = f"api:{today}:facts:{args.evidence_id}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    schema = read_json(SCHEMA_PATH)

    r = requests.get(args.url, timeout=30)
    r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    if "pdf" in content_type.lower() or args.url.lower().endswith(".pdf"):
        raise SystemExit("v1 supports HTML only. (PDF parsing to be added later)")

    text = strip_text(r.text)

    prompt = f"""
You are extracting factual records for the Hakone Ekiden domain SSOT (A方式).
Return ONLY JSON (no markdown), matching this JSON Schema:
{json.dumps(schema, ensure_ascii=False)}

Rules:
- Create claims as atomic facts. Each claim MUST include evidence_refs containing \"{args.evidence_id}\".
- Prefer stable IDs. Use these keys:
  evidence_id, entity_id, event_id, claim_id
- For every claim, include: claim_id, key, value, evidence_refs, event_refs, entity_refs, meta
- meta must include: schema_id=\"hakone-e2.domain\", schema_version=\"v1\", run_id=\"{run_id}\", created_at=\"{today}\", updated_at=\"{today}\"
- Use event_id \"{args.event_id}\" if it is not \"__UNKNOWN__\", otherwise create one event.
Input evidence URL: {args.url}
Evidence text:
{text}
"""

    extracted = call_model_json_object(args.model, prompt)
    write_json(run_dir / "extracted.json", extracted)

    try:
        validate(instance=extracted, schema=schema)
        validated = extracted
    except Exception:
        repair_prompt = f"""
Fix the following JSON to match the JSON Schema exactly. Return ONLY JSON.
Schema:
{json.dumps(schema, ensure_ascii=False)}

JSON:
{json.dumps(extracted, ensure_ascii=False)}
"""
        repaired = call_model_json_object(args.model, repair_prompt)
        validate(instance=repaired, schema=schema)
        validated = repaired

    write_json(run_dir / "validated.json", validated)

    evi = load_container(DOMAIN_DIR / "e2_evidence_v1.json")
    ent = load_container(DOMAIN_DIR / "e2_entities_v1.json")
    evt = load_container(DOMAIN_DIR / "e2_events_v1.json")
    clm = load_container(DOMAIN_DIR / "e2_claims_v1.json")

    for obj in validated.get("evidence", []):
        upsert_by_id(evi["items"], "evidence_id", obj)
    for obj in validated.get("entities", []):
        upsert_by_id(ent["items"], "entity_id", obj)
    for obj in validated.get("events", []):
        upsert_by_id(evt["items"], "event_id", obj)
    for obj in validated.get("claims", []):
        upsert_by_id(clm["items"], "claim_id", obj)

    by_key = {}
    conflicts = []
    for c in clm["items"]:
        if not isinstance(c, dict):
            continue
        k = c.get("key")
        v = c.get("value")
        if not k:
            continue
        if k in by_key and by_key[k] != v:
            conflicts.append({"key": k, "value_a": by_key[k], "value_b": v})
        else:
            by_key[k] = v

    write_json(run_dir / "conflicts.json", {"conflicts": conflicts})

    write_json(DOMAIN_DIR / "e2_evidence_v1.json", evi)
    write_json(DOMAIN_DIR / "e2_entities_v1.json", ent)
    write_json(DOMAIN_DIR / "e2_events_v1.json", evt)
    write_json(DOMAIN_DIR / "e2_claims_v1.json", clm)

    (run_dir / "patch_preview.md").write_text(
        f"- run_id: {run_id}\\n- url: {args.url}\\n- conflicts: {len(conflicts)}\\n",
        encoding="utf-8",
    )

    print(f"OK run_id={run_id} conflicts={len(conflicts)} mode={args.mode}")


if __name__ == "__main__":
    main()
