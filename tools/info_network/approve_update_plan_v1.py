#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def approve_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    plan["questions"] = []
    plan["notes"] = (
        plan.get("notes", "")
        + "\n\n[approved] Owner approved suggestions; questions cleared."
    ).strip()
    return plan


def reject_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    plan["questions"] = []
    plan["supersedes"] = []
    plan["obsolete"] = []
    plan["notes"] = (
        plan.get("notes", "")
        + "\n\n[rejected] Owner rejected supersedes/obsolete; questions cleared."
    ).strip()
    return plan


def interactive_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    questions = plan.get("questions", []) or []
    if not questions:
        return approve_plan(plan)

    print("Interactive approval (y=approve all, n=reject all).")
    for idx, q in enumerate(questions, 1):
        print(f"[Q{idx}] {q.get('question')}")
        ans = input("Approve? (y/n): ").strip().lower()
        if ans not in {"y", "yes"}:
            return reject_plan(plan)
    return approve_plan(plan)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Convert a suggestion update_plan into an approved plan (questions cleared). Does NOT apply."
    )
    ap.add_argument("--input", required=True, help="suggestion update_plan JSON")
    ap.add_argument("--output", required=True, help="approved plan output JSON")
    ap.add_argument(
        "--mode",
        choices=["approve", "reject", "interactive"],
        default="interactive",
        help="approval mode (default: interactive)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show summary without writing output",
    )
    args = ap.parse_args()

    plan_path = Path(args.input)
    out_path = Path(args.output)
    plan = load_json(plan_path)

    before_q = len(plan.get("questions", []) or [])
    if args.mode == "approve":
        plan = approve_plan(plan)
    elif args.mode == "reject":
        plan = reject_plan(plan)
    else:
        plan = interactive_plan(plan)

    after_q = len(plan.get("questions", []) or [])
    print(
        f"questions: before={before_q}, after={after_q}, "
        f"supersedes={len(plan.get('supersedes', []))}, obsolete={len(plan.get('obsolete', []))}"
    )

    if args.dry_run:
        print("dry-run: not writing output")
        return

    save_json(out_path, plan)
    print(f"Wrote approved plan: {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
