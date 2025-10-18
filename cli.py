#!/usr/bin/env python
"""
使い方:
  python cli.py <objective_id> <メッセージ>
  python cli.py answer "今のPhaseは？" [--ai] [--budget 2000] [--no-json]
  python cli.py state-update [--ai] [--print] [--decisions-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

# src/ を import パスへ追加
sys.path.append(str(pathlib.Path(__file__).resolve().parent / "src"))
from core import ask_openai

_SUPPORTED_COMMANDS = {"answer", "state-update"}


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] not in _SUPPORTED_COMMANDS:
        # 互換維持: 従来の CLI は早期リターン
        obj_id = sys.argv[1]
        user_msg = " ".join(sys.argv[2:])
        print(ask_openai(obj_id, user_msg))
        return

    parser = _build_parser()
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if args.command == "answer":
        _handle_answer(args)
    elif args.command == "state-update":
        _handle_state_update(args)
    else:
        parser.print_help()
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    answer = subparsers.add_parser("answer", help="SSOTに基づく質問応答を実行")
    answer.add_argument("question", help="質問文")
    answer.add_argument("--ai", action="store_true", help="LLMモードを有効化")
    answer.add_argument(
        "--budget",
        type=int,
        default=2000,
        help="SSOT抜粋の最大文字数（デフォルト: 2000）",
    )
    answer.add_argument(
        "--no-json",
        action="store_true",
        help="JSONではなく短文サマリを出力",
    )

    state = subparsers.add_parser(
        "state-update",
        help="Decision Log から STATE update 草案を生成",
    )
    state.add_argument("--ai", action="store_true", help="LLMモードを有効化")
    state.add_argument(
        "--print",
        dest="print_body",
        action="store_true",
        help="生成した本文を標準出力に表示",
    )
    state.add_argument(
        "--decisions-dir",
        default="reports/decisions",
        help="Decision Log のディレクトリ（デフォルト: reports/decisions）",
    )
    state.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Decision Log の取得件数（デフォルト: 10）",
    )

    return parser


def _handle_answer(args: argparse.Namespace) -> None:
    from core.grounded_answer import grounded_answer

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
    from core.state_drafter import draft_state

    repo_root = pathlib.Path(__file__).resolve().parent

    result = draft_state(
        decisions_dir=args.decisions_dir,
        max_items=args.max_items,
        use_ai=args.ai,
    )
    target_path = repo_root / result["path"]
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

    # 最後に生成ファイルの絶対パスを単独行で表示（スクリプトから取得しやすいように）
    print(str(target_path))


if __name__ == "__main__":
    main()
