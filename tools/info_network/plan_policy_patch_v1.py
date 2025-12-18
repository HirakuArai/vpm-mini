#!/usr/bin/env python3
"""
Patch approved_plan.json:
- enforce additive_only (clear supersedes/obsolete)
- drop add entries whose id matches substrings or regex patterns
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_id(x: Any) -> Optional[str]:
    if isinstance(x, dict):
        return x.get("id") or x.get("node_id") or x.get("uid")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="Path to approved_plan.json")
    ap.add_argument(
        "--out", default="", help="Optional output path (default: in-place)"
    )
    ap.add_argument(
        "--additive-only",
        action="store_true",
        help="Clear supersedes/obsolete, ensure questions empty",
    )
    ap.add_argument(
        "--drop-add-id-contains",
        action="append",
        default=[],
        help="Drop add entries if id contains substring",
    )
    ap.add_argument(
        "--drop-add-id-regex",
        action="append",
        default=[],
        help="Drop add entries if id matches regex",
    )
    args = ap.parse_args()

    p = Path(args.plan)
    d: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))

    if args.additive_only:
        d["questions"] = []
        d["supersedes"] = []
        d["obsolete"] = []

    subs: List[str] = args.drop_add_id_contains or []
    regs: List[re.Pattern] = [re.compile(r) for r in (args.drop_add_id_regex or [])]

    adds = d.get("add", []) or []
    kept, dropped = [], []
    for a in adds:
        aid = get_id(a) or ""
        drop = False
        if aid:
            for s in subs:
                if s and s in aid:
                    drop = True
                    break
            if not drop:
                for r in regs:
                    if r.search(aid):
                        drop = True
                        break
        if drop:
            dropped.append(aid)
        else:
            kept.append(a)
    d["add"] = kept

    out_path = Path(args.out) if args.out else p
    out_path.write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"patched: {out_path}")
    print(f"add: {len(adds)} -> {len(kept)} (dropped {len(dropped)})")
    if dropped:
        print("dropped_ids (first 20):")
        for x in dropped[:20]:
            print(" -", x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
