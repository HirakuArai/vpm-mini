#!/usr/bin/env python3
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def load_list(path: Path) -> List[Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("nodes", "relations", "items", "data"):
            v = obj.get(k)
            if isinstance(v, list):
                return v
    raise ValueError(f"Unsupported JSON shape: {path}")

def get_id(x: Any) -> Optional[str]:
    if isinstance(x, dict):
        return x.get("id") or x.get("node_id") or x.get("uid")
    return None

def rel_endpoints(r: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    a = r.get("from") or r.get("src") or r.get("source")
    b = r.get("to") or r.get("dst") or r.get("target")
    return a, b

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--relations", required=True)
    ap.add_argument("--fail-on-dup-rel-ids", action="store_true", help="Also fail on duplicate relation ids (if present)")
    args = ap.parse_args()

    nodes_p = Path(args.nodes)
    rels_p = Path(args.relations)

    # Level0: parse ok (json.loads above)
    nodes = load_list(nodes_p)
    rels = load_list(rels_p)

    # Level2: ID uniqueness + endpoint existence
    node_ids = [get_id(n) for n in nodes if get_id(n)]
    node_id_counts = Counter(node_ids)
    dup_node_ids = [i for i, c in node_id_counts.items() if c > 1]

    missing_endpoints: List[Tuple[str, str]] = []
    for r in rels:
        if not isinstance(r, dict):
            continue
        a, b = rel_endpoints(r)
        if a and a not in node_id_counts:
            missing_endpoints.append(("from", a))
        if b and b not in node_id_counts:
            missing_endpoints.append(("to", b))

    dup_rel_ids: List[str] = []
    if args.fail_on_dup_rel_ids:
        rel_ids = [get_id(r) for r in rels if isinstance(r, dict) and get_id(r)]
        rel_id_counts = Counter(rel_ids)
        dup_rel_ids = [i for i, c in rel_id_counts.items() if c > 1]

    print("nodes_count:", len(nodes), "node_ids:", len(node_id_counts))
    print("rels_count :", len(rels))
    print("dup_node_ids:", len(dup_node_ids))
    print("missing_endpoints:", len(missing_endpoints))
    if args.fail_on_dup_rel_ids:
        print("dup_rel_ids:", len(dup_rel_ids))

    ok = True
    if dup_node_ids:
        ok = False
        print("ERROR dup_node_ids examples:", dup_node_ids[:20])
    if missing_endpoints:
        ok = False
        print("ERROR missing_endpoints examples:", missing_endpoints[:40])
    if args.fail_on_dup_rel_ids and dup_rel_ids:
        ok = False
        print("ERROR dup_rel_ids examples:", dup_rel_ids[:20])

    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
