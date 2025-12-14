#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def normalize_source_refs(val: Any) -> Any:
    if not isinstance(val, list):
        return val
    refs = [r for r in val if isinstance(r, dict)]
    return sorted(refs, key=lambda r: (r.get("kind", ""), r.get("value", "")))


def normalize_list(val: Any) -> Any:
    if not isinstance(val, list):
        return val
    try:
        return sorted(val)
    except Exception:
        return val


def normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in node.items():
        if k in {"updated_at", "created_at"}:
            continue
        out[k] = v
    if "source_refs" in out:
        out["source_refs"] = normalize_source_refs(out["source_refs"])
    for k in ("tags", "hints"):
        if k in out:
            out[k] = normalize_list(out[k])
    return out


def normalize_relation(rel: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in rel.items():
        if k in {"updated_at", "created_at"}:
            continue
        out[k] = v
    if "source_refs" in out:
        out["source_refs"] = normalize_source_refs(out["source_refs"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate update_plan v0.1 (id-based add/update with no-op detection)."
    )
    ap.add_argument("--canonical-nodes", required=True)
    ap.add_argument("--canonical-relations", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    canonical_nodes = load_json(Path(args.canonical_nodes), [])
    canonical_rels = load_json(Path(args.canonical_relations), [])
    cn = {
        n.get("id"): n for n in canonical_nodes if isinstance(n, dict) and n.get("id")
    }
    cr = {r.get("id"): r for r in canonical_rels if isinstance(r, dict) and r.get("id")}

    snap = load_json(Path(args.snapshot), {})
    aya = snap.get("aya_output", {})
    snodes = aya.get("info_nodes", []) or []
    srels = aya.get("info_relations", []) or []

    add = []
    update = []
    matches = []
    noop_nodes: List[str] = []
    for n in snodes:
        nid = n.get("id")
        if not nid:
            continue
        if nid in cn:
            existing_norm = normalize_node(cn[nid])
            incoming_norm = normalize_node(n)
            if existing_norm == incoming_norm:
                noop_nodes.append(nid)
            else:
                update.append(n)
            matches.append({"new": nid, "existing": [nid]})
        else:
            add.append(n)
            matches.append({"new": nid, "existing": []})

    add_rels = []
    update_rels = []
    noop_rels: List[str] = []
    for r in srels:
        rid = r.get("id")
        if not rid:
            continue
        if rid in cr:
            existing_norm = normalize_relation(cr[rid])
            incoming_norm = normalize_relation(r)
            if existing_norm == incoming_norm:
                noop_rels.append(rid)
            else:
                update_rels.append(r)
        else:
            add_rels.append(r)

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    out = {
        "project_id": "hakone-e2",
        "source_snapshot_id": Path(args.snapshot).name,
        "generated_at": now,
        "matches": matches,
        "add": add,
        "add_relations": add_rels,
        "update": update,
        "update_relations": update_rels,
        "obsolete": [],
        "obsolete_relations": [],
        "supersedes": [],
        "notes": "v0.1: id一致なら更新、内容同一ならnoop。意味判断はしない。",
        "noop": noop_nodes,
        "noop_relations": noop_rels,
    }

    save_json(Path(args.output), out)

    print(
        f"add nodes={len(add)}, update nodes={len(update)}, noop nodes={len(noop_nodes)}"
    )
    print(
        f"add rels={len(add_rels)}, update rels={len(update_rels)}, noop rels={len(noop_rels)}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
