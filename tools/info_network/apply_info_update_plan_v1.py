#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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


def safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", s)


def make_supersedes_rel(
    project_id: str,
    new_id: str,
    old_id: str,
    source_snapshot_id: str,
    generated_at: str,
) -> Dict[str, Any]:
    rid = f"{project_id}:relation:supersedes:{safe_id(new_id)}__{safe_id(old_id)}"
    return {
        "id": rid,
        "project_id": project_id,
        "type": "supersedes",
        "from": new_id,
        "to": old_id,
        "strength": 1.0,
        "status": "active",
        "source_refs": [{"kind": "plan", "value": source_snapshot_id}],
        "created_at": generated_at,
        "updated_at": generated_at,
    }


def upsert(
    items: List[Dict[str, Any]], incoming: List[Dict[str, Any]], key: str = "id"
) -> tuple[List[Dict[str, Any]], int, int]:
    index = {i.get(key): i for i in items if isinstance(i, dict) and i.get(key)}
    added = updated = 0
    for it in incoming:
        if not isinstance(it, dict):
            continue
        kid = it.get(key)
        if not kid:
            continue
        if kid in index:
            index[kid] = it
            updated += 1
        else:
            index[kid] = it
            added += 1
    return list(index.values()), added, updated


def apply_obsolete(
    ids: List[str], existing: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], int]:
    index = {i.get("id"): i for i in existing if isinstance(i, dict) and i.get("id")}
    obsoleted = 0
    for oid in ids:
        if oid in index:
            obj = index[oid]
            if isinstance(obj, dict):
                obj["status"] = "obsolete"
                index[oid] = obj
                obsoleted += 1
    return list(index.values()), obsoleted


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Apply info_update_plan_v1 to canonical nodes/relations."
    )
    ap.add_argument("--plan", required=True)
    ap.add_argument("--nodes", default="data/hakone-e2/info_nodes_v1.json")
    ap.add_argument("--relations", default="data/hakone-e2/info_relations_v1.json")
    args = ap.parse_args()

    plan_path = Path(args.plan)
    nodes_path = Path(args.nodes)
    relations_path = Path(args.relations)

    plan = load_json(plan_path, {})
    project_id = plan.get("project_id", "")
    source_snapshot_id = plan.get("source_snapshot_id", plan_path.name)
    generated_at = plan.get("generated_at") or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    nodes = load_json(nodes_path, [])
    relations = load_json(relations_path, [])

    # Nodes: add + update
    nodes, n_added1, n_updated1 = upsert(nodes, plan.get("add", []) or [])
    nodes, n_added2, n_updated2 = upsert(nodes, plan.get("update", []) or [])

    # Nodes: obsolete
    nodes, n_obsoleted = apply_obsolete(plan.get("obsolete", []) or [], nodes)

    # Relations: add + update
    relations, r_added1, r_updated1 = upsert(
        relations, plan.get("add_relations", []) or []
    )
    relations, r_added2, r_updated2 = upsert(
        relations, plan.get("update_relations", []) or []
    )

    # Relations: obsolete
    relations, r_obsoleted = apply_obsolete(
        plan.get("obsolete_relations", []) or [], relations
    )

    # Supersedes -> deterministic relations
    sup_entries = plan.get("supersedes", []) or []
    sup_rels: List[Dict[str, Any]] = []
    for entry in sup_entries:
        if not isinstance(entry, dict):
            continue
        new_id = entry.get("new")
        olds = entry.get("old") or []
        if not new_id or not isinstance(olds, list):
            continue
        for old_id in olds:
            if not old_id:
                continue
            sup_rels.append(
                make_supersedes_rel(
                    project_id, new_id, old_id, source_snapshot_id, generated_at
                )
            )
    sup_added = sup_updated = 0
    if sup_rels:
        relations, sup_added, sup_updated = upsert(relations, sup_rels, "id")

    save_json(nodes_path, nodes)
    save_json(relations_path, relations)

    print(
        f"nodes: added {n_added1+n_added2}, updated_add {n_updated1}, updated {n_updated2}, obsoleted {n_obsoleted}, total {len(nodes)}"
    )
    print(
        f"relations: added {r_added1+r_added2}, updated_add {r_updated1}, updated {r_updated2}, obsoleted {r_obsoleted}, supersedes_added {sup_added}, total {len(relations)}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
