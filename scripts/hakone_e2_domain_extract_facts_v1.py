import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Set

import requests
from jsonschema import validate

from openai import OpenAI

DOMAIN_DIR = Path("data/hakone-e2/domain")
RUNS_DIR = Path("reports/hakone-e2/runs")
SCHEMA_PATH = Path("schemas/hakone-e2/domain_extract_facts_patch_v1.schema.json")


def load_entity_registry_for_prompt():
    # Load existing entities (A(domain) registry). We will NOT create new entities in facts lane v1.4.
    ent = load_container(DOMAIN_DIR / "e2_entities_v1.json")
    items = ent.get("items", [])
    reg = []
    for x in items:
        if not isinstance(x, dict):
            continue
        reg.append(
            {
                "entity_id": x.get("entity_id"),
                "entity_type": x.get("entity_type"),
                "name": x.get("name"),
                "aliases": x.get("aliases", []),
            }
        )
    # keep prompt small-ish
    return reg[:500]


ALLOWED_EVIDENCE_TYPES = {"official", "semi_official", "media", "other"}


def normalize_evidence_type(e: dict) -> str:
    """
    Normalize evidence.type into controlled vocabulary:
      official | semi_official | media | other
    """
    t = (e.get("type") or "").strip().lower()
    pub = (e.get("publisher") or "").strip()
    url = (e.get("url") or "").strip().lower()

    # If already in controlled vocab, keep
    if t in ALLOWED_EVIDENCE_TYPES:
        return t

    # Heuristics (quality-first, conservative):
    # Official-ish sources
    if "hakone-ekiden.jp" in url:
        return "official"
    if "kgrr.org" in url or "kgrr" in pub:
        return "official"

    # Semi-official: broadcaster official pages, etc.
    if "ntv.co.jp/hakone" in url or "日本テレビ" in pub or pub.upper() == "NTV":
        return "semi_official"

    # Media
    if "nikkansports.com" in url or "日刊スポーツ" in pub:
        return "media"

    # Fallback: if it was "webpage" etc, map to other
    return "other"


_time_hms_pat = re.compile(r"^\s*(\d{1,2}):(\d{2}):(\d{2})\s*$")
_time_jp_pat = re.compile(r"^\s*(\d{1,2})\s*時間\s*(\d{1,2})\s*分\s*(\d{1,2})\s*秒\s*$")


def normalize_total_time(value: dict) -> None:
    """
    Normalize value.total_time to HH:MM:SS if possible.
    Preserve original string in total_time_display if changed.
    """
    if not isinstance(value, dict):
        return
    t = value.get("total_time")
    if not isinstance(t, str) or not t.strip():
        return

    raw = t.strip()

    m = _time_hms_pat.match(raw)
    if m:
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        value["total_time"] = f"{hh:02d}:{mm:02d}:{ss:02d}"
        return

    m = _time_jp_pat.match(raw)
    if m:
        hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        value["total_time_display"] = raw
        value["total_time"] = f"{hh:02d}:{mm:02d}:{ss:02d}"
        return


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
    # key uniqueness inside this patch (avoid pseudo-conflicts)
    keys = [c.get("key") for c in validated["claims"] if isinstance(c, dict)]
    keys = [k for k in keys if isinstance(k, str) and k]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise ValueError(f"duplicate claim.key in patch: {dup[:10]}")


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

    entity_registry = load_entity_registry_for_prompt()

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
- Create claims as atomic facts (1 claim = 1断定). Each claim MUST include evidence_refs containing "{args.evidence_id}".
- IMPORTANT: claim.key MUST be unique per claim. Do NOT reuse a generic key for multiple rows.
  - Use a normalized key encoding at least: event (or locked event_id), rank (if ranking), and team identifier in value.
- Prefer stable IDs. Use these keys: evidence_id, entity_id, event_id, claim_id
- meta must include:
  schema_id="hakone-e2.domain", schema_version="v1", run_id="{run_id}", created_at="{today}", updated_at="{today}"

Evidence policy:
- evidence.type must be one of: official | semi_official | media | other

Entity policy (QUALITY-FIRST):
- Do NOT invent new entity_id values in this lane.
- You may only reference entities that already exist in the registry provided below.
- If you cannot confidently map a team/person to an existing entity_id, set entity_refs to an empty list [].
- Do NOT create entities of type "event". Events belong in events[].

Event handling:
- If event_id "{args.event_id}" is not "__UNKNOWN__", ALL claims must use event_refs=["{args.event_id}"] exactly.
  In that case, return events as an empty list [] (do NOT create new events).
- If event_id is "__UNKNOWN__", you may create one event in events[] and reference it from claims.

Existing entity registry (use ONLY these entity_id values if needed):
{json.dumps(entity_registry, ensure_ascii=False)}

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

    # Event lock: if event_id is provided, require claims to reference ONLY that event_id, and ignore model-created events
    locked_event_id = args.event_id
    if locked_event_id != "__UNKNOWN__":
        for c in validated.get("claims", []):
            if not isinstance(c, dict):
                continue
            evs = c.get("event_refs", [])
            if evs != [locked_event_id]:
                raise ValueError(
                    f"claim {c.get('claim_id')} event_refs must be exactly [{locked_event_id}] when event_id is provided"
                )
        # normalize events list to empty to avoid accidental upsert of wrong event
        validated["events"] = []

    # Normalize evidence.type and time formats (quality-first)
    # - evidence.type -> controlled vocab: official|semi_official|media|other
    # - total_time -> HH:MM:SS (preserve original in total_time_display if changed)
    for e in validated.get("evidence", []):
        if isinstance(e, dict):
            e["type"] = normalize_evidence_type(e)
    for c in validated.get("claims", []):
        if isinstance(c, dict) and isinstance(c.get("value"), dict):
            normalize_total_time(c["value"])
    write_json(run_dir / "validated.json", validated)

    # Entity registry lock (quality-first): do not allow new entity_ids to be introduced by this lane.
    existing_ent = load_container(DOMAIN_DIR / "e2_entities_v1.json")
    existing_ids = {
        x.get("entity_id") for x in existing_ent.get("items", []) if isinstance(x, dict)
    }
    for e in validated.get("entities", []):
        if not isinstance(e, dict):
            continue
        eid = e.get("entity_id")
        if eid and eid not in existing_ids:
            raise ValueError(f"new entity_id not allowed in facts lane v1.4: {eid}")

    evi = load_container(DOMAIN_DIR / "e2_evidence_v1.json")

    # best-effort normalize existing domain evidence types into controlled vocab
    for e in evi.get("items", []):
        if isinstance(e, dict):
            e["type"] = normalize_evidence_type(e)
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

    # Human-readable conflict summary (quality-first)
    # We DO NOT auto-resolve conflicts in v1; we only suggest by evidence type priority.
    # Priority: official > semi_official > media > other
    priority = {"official": 4, "semi_official": 3, "media": 2, "other": 1}

    # Build evidence type map from current domain evidence items (best-effort)
    evi_type = {}
    for e in evi["items"]:
        if isinstance(e, dict) and e.get("evidence_id"):
            et = e.get("type") or "other"
            evi_type[e["evidence_id"]] = et

    # For each conflicting key, list candidate claim_ids grouped by value
    # and output a recommended candidate (best-effort) by max evidence priority.
    lines = []
    lines.append("# conflicts summary (v1)\n")
    lines.append(f"- conflicts: {len(conflicts)}\n")
    lines.append(
        "## Priority (best-effort)\n- official > semi_official > media > other\n"
    )

    # We need richer info than current conflicts list (which only has value_a/value_b),
    # so we re-scan claims for each key.
    key_to_claims = defaultdict(list)
    for c in clm["items"]:
        if not isinstance(c, dict):
            continue
        k = c.get("key")
        if not k:
            continue
        key_to_claims[k].append(c)

    conflict_keys = sorted(
        {c["key"] for c in conflicts if isinstance(c, dict) and c.get("key")}
    )
    for k in conflict_keys:
        candidates = key_to_claims.get(k, [])
        lines.append(f"\n---\n## key: {k}\n")
        # group by value
        by_val = defaultdict(list)
        for c in candidates:
            by_val[str(c.get("value"))].append(c)
        # compute recommendation by best evidence priority
        best_score = -1
        best_claim = None
        for c in candidates:
            refs = c.get("evidence_refs") or []
            score = 0
            for r in refs:
                score = max(score, priority.get(evi_type.get(r, "other"), 1))
            if score > best_score:
                best_score = score
                best_claim = c
        if best_claim:
            lines.append(
                f"- recommended_claim_id: {best_claim.get('claim_id')} (score={best_score})\n"
            )

        lines.append("- candidates:\n")
        for v, cs in by_val.items():
            lines.append(f"  - value: {v[:120]}\n")
            for c in cs:
                refs = c.get("evidence_refs") or []
                types = [evi_type.get(r, "other") for r in refs]
                lines.append(
                    f"    - claim_id: {c.get('claim_id')} evidence: {refs} types: {types}\n"
                )

    (run_dir / "conflicts_summary.md").write_text("".join(lines), encoding="utf-8")

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
