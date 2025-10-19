#!/usr/bin/env python
"""
使い方:
  python cli.py <objective_id> <メッセージ>
  python cli.py answer "今のPhaseは？" [--ai] [--budget 2000] [--no-json]
  python cli.py state-update [--ai] [--print] [--decisions-dir PATH]
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

# src/ を import パスへ追加
sys.path.append(str(pathlib.Path(__file__).resolve().parent / "src"))
from core import ask_openai
from core.grounded_answer import grounded_answer
from core.state_drafter import draft_state


def _maybe_handle_subcommand() -> bool:
    if len(sys.argv) < 2:
        return False

    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="subcmd")

    p_ans = subparsers.add_parser("answer", add_help=False)
    p_ans.add_argument("question", nargs="+")
    p_ans.add_argument("--ai", action="store_true")
    p_ans.add_argument("--budget", type=int, default=2000)
    p_ans.add_argument("--no-json", action="store_true")

    p_state = subparsers.add_parser("state-update", add_help=False)
    p_state.add_argument("--ai", action="store_true")
    p_state.add_argument("--print", dest="prn", action="store_true")
    p_state.add_argument("--decisions-dir", default="reports/decisions")
    p_state.add_argument("--max-items", type=int, default=10)

    p_plan = subparsers.add_parser("plan", add_help=False)
    p_plan.add_argument("--ai", action="store_true")
    p_plan.add_argument("--limit", type=int, default=5)
    p_plan.add_argument("--out", dest="out_path", default="out/next_actions.json")

    try:
        ns, _ = parser.parse_known_args()
    except SystemExit:
        return False

    if ns.subcmd == "answer":
        question_text = " ".join(getattr(ns, "question", []))
        if not question_text:
            return False
        args = argparse.Namespace(
            question=question_text,
            ai=getattr(ns, "ai", False),
            budget=getattr(ns, "budget", 2000),
            no_json=getattr(ns, "no_json", False),
        )
        _handle_answer(args)
        return True

    if ns.subcmd == "state-update":
        args = argparse.Namespace(
            ai=getattr(ns, "ai", False),
            print_body=getattr(ns, "prn", False),
            decisions_dir=getattr(ns, "decisions_dir", "reports/decisions"),
            max_items=getattr(ns, "max_items", 10),
        )
        _handle_state_update(args)
        return True

    if ns.subcmd == "plan":
        args = argparse.Namespace(
            ai=getattr(ns, "ai", False),
            limit=max(1, int(getattr(ns, "limit", 5) or 5)),
            out_path=getattr(ns, "out_path", "out/next_actions.json"),
        )
        _handle_plan(args)
        return True

    return False


def _handle_answer(args: argparse.Namespace) -> None:
    result = grounded_answer(args.question, use_ai=args.ai, budget=args.budget)
    if args.no_json:
        print(result.get("answer", ""))
        sources = result.get("sources", [])
        if sources:
            print("sources:", ", ".join(sources))
        print(f"confidence: {result.get('confidence', 0.0)}")
        unknown = result.get("unknown_fields", [])
        if unknown:
            print("unknown_fields:", ", ".join(unknown))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _handle_state_update(args: argparse.Namespace) -> None:
    repo_root = pathlib.Path(__file__).resolve().parent

    result = draft_state(
        decisions_dir=args.decisions_dir,
        max_items=args.max_items,
        use_ai=args.ai,
    )
    raw_path = result.get("path") or ""
    target_path = pathlib.Path(raw_path)
    if not target_path.is_absolute():
        target_path = repo_root / target_path
    if target_path.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = target_path.parent / f"update_{timestamp}.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(result["body"], encoding="utf-8")

    meta = result.get("meta") or {}
    if args.ai and not meta.get("ai_used", False):
        print("AI draft unavailable or skipped; rule-based template used.")

    print(f"Generated {target_path}")

    if args.print_body:
        print("---")
        print(result["body"])

    sources = result.get("sources", [])
    if sources:
        print("sources:", ", ".join(sources))

    print(str(target_path))


def _handle_plan(args: argparse.Namespace) -> None:
    from core.plan_suggester import suggest_plan

    out_path = pathlib.Path(args.out_path)
    try:
        plan = suggest_plan(use_ai=args.ai, limit=args.limit)
    except Exception as exc:  # pragma: no cover - defensive path
        print(f"Plan generation failed: {exc}")
        return

    actions = plan.get("next_actions") or []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if actions:
        first_title = actions[0].get("title", "")
        print(f"Saved {len(actions)} actions to {out_path} (top: {first_title})")
    else:
        print(f"Saved empty plan to {out_path}")


def main() -> None:
    if _maybe_handle_subcommand():
        return

    if len(sys.argv) < 3:
        print("Usage: python cli.py <objective_id> <message>")
        sys.exit(1)

    obj_id = sys.argv[1]
    user_msg = " ".join(sys.argv[2:])
    print(ask_openai(obj_id, user_msg))


if __name__ == "__main__":
    main()
