import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Set

import requests
from jsonschema import validate

from openai import OpenAI

DOMAIN_DIR = Path("data/hakone-e2/domain")
RUNS_DIR = Path("reports/hakone-e2/runs")
SCHEMA_PATH = Path("schemas/hakone-e2/domain_extract_facts_patch_v1.schema.json")

REQUIRED_META_KEYS = {
    "schema_id",
    "schema_version",
    "run_id",
    "created_at",
    "updated_at",
}


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
        raise RuntimeError("No output_text; SDK shape changed. Please update parser.")
    return json.loads(out)


def _expect_keys(obj: Dict[str, Any], keys: Set[str], label: str):
    miss = [k for k in keys if k not in obj]
    if miss:
        raise ValueError(f"{label} missing keys: {miss}")


def enforce_quality_gate(validated: Dict[str, Any], evidence_id: str):
    # Ensure patch has required top-level arrays
    for k in ("evidence", "entities", "events", "claims"):
        if k not in validated or not isinstance(validated[k], list):
            raise ValueError(f"validated.{k} must be a list")

    # claim gate: must have evidence_refs including evidence_id
    for c in validated["claims"]:
        if not isinstance(c, dict):
            raise ValueError("claim must be object")
        _expect_keys(
            c,
            {
                "claim_id",
                "key",
                "value",
                "evidence_refs",
                "event_refs",
                "entity_refs",
                "meta",
            },
            "claim",
        )
        if not isinstance(c["evidence_refs"], list) or not c["evidence_refs"]:
            raise ValueError(f"claim {c.get('claim_id')} evidence_refs empty")
        if evidence_id not in c["evidence_refs"]:
            raise ValueError(
                f"claim {c.get('claim_id')} evidence_refs must include {evidence_id}"
            )

        if not isinstance(c["event_refs"], list):
            raise ValueError(f"claim {c.get('claim_id')} event_refs must be list")
        if not isinstance(c["entity_refs"], list):
            raise ValueError(f"claim {c.get('claim_id')} entity_refs must be list")
        if not isinstance(c["meta"], dict):
            raise ValueError(f"claim {c.get('claim_id')} meta must be object")
        _expect_keys(c["meta"], REQUIRED_META_KEYS, f"claim {c.get('claim_id')}.meta")


def resolve_refs_after_upsert(evi_items, ent_items, evt_items, clm_items):
    evi_ids = {x.get("evidence_id") for x in evi_items if isinstance(x, dict)}
    ent_ids = {x.get("entity_id") for x in ent_items if isinstance(x, dict)}
    evt_ids = {x.get("event_id") for x in evt_items if isinstance(x, dict)}

    bad = []
    for c in clm_items:
        if not isinstance(c, dict):
            continue
        cid = c.get("claim_id")
        for ref in c.get("evidence_refs", []) or []:
            if ref not in evi_ids:
                bad.append((cid, "evidence_refs", ref))
        for ref in c.get("event_refs", []) or []:
            if ref not in evt_ids:
                bad.append((cid, "event_refs", ref))
        for ref in c.get("entity_refs", []) or []:
            if ref not in ent_ids:
                bad.append((cid, "entity_refs", ref))

    if bad:
        raise ValueError(f"Reference resolution failed (first 20): {bad[:20]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--evidence-id", required=True)
    ap.add_argument("--event-id", default="__UNKNOWN__")
    ap.add_argument("--mode", choices=["dry-run", "pr"], default="dry-run")
    ap.add_argument("--model", default="gpt-4.1")
    args = ap.parse_args()

    today = date.today().isoformat()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"api:{today}:facts:{args.evidence_id}:{ts}"
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
- Create claims as atomic facts. Each claim MUST include evidence_refs containing "{args.evidence_id}".
- Prefer stable IDs. Use these keys: evidence_id, entity_id, event_id, claim_id
- meta must include:
  schema_id="hakone-e2.domain", schema_version="v1", run_id="{run_id}", created_at="{today}", updated_at="{today}"
- If event_id "{args.event_id}" is not "__UNKNOWN__", use it; otherwise create one event_id.

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

    enforce_quality_gate(validated, args.evidence_id)

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

    resolve_refs_after_upsert(evi["items"], ent["items"], evt["items"], clm["items"])

    write_json(DOMAIN_DIR / "e2_evidence_v1.json", evi)
    write_json(DOMAIN_DIR / "e2_entities_v1.json", ent)
    write_json(DOMAIN_DIR / "e2_events_v1.json", evt)
    write_json(DOMAIN_DIR / "e2_claims_v1.json", clm)

    (run_dir / "patch_preview.md").write_text(
        f"- run_id: {run_id}\\n- url: {args.url}\\n- conflicts: {len(conflicts)}\\n",
        encoding="utf-8",
    )

    print(f"RUN_ID={run_id}")
    print(f"OK run_id={run_id} conflicts={len(conflicts)} mode={args.mode}")


if __name__ == "__main__":
    main()
