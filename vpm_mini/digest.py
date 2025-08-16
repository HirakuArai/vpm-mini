# vpm_mini/digest.py
from __future__ import annotations
import argparse
import sys
from datetime import datetime
from pathlib import Path
from .summary import build_session_digest, prepend_memory, summarize_last_session
from .logs import extract_text_from_logs
from .egspace import get_stats


def _iso_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def render_digest_md(state: dict, stats: dict | None = None) -> str:
    """docs/sessions/*-digest.md 向けのMarkdownを返す。"""
    lines = []
    lines.append(f"# Session Digest — {_iso_date()}\n")
    lines.append("## 概要（≤400字）\n")
    lines.append(state.get("summary_ja_<=400chars", "") + "\n")

    def section(title: str, key: str):
        lines.append(f"\n## {title}\n")
        val = state.get(key, "")
        if isinstance(val, str) and val.strip():
            lines.append(val + "\n")
        elif isinstance(val, list) and val:
            for it in val:
                lines.append(f"- {it}")
            lines.append("")
        else:
            lines.append("(なし)\n")

    section("現在地 (C)", "C")
    section("目的地 (G)", "G")
    section("差分 δ", "delta")
    section("決定", "decisions")
    section("未決 / Open", "open_questions")
    section("TODO / 次の一手", "todos")
    section("リスク", "risks")

    # Add progress snapshot if stats provided
    if stats:
        lines.append("\n---\n")
        total = stats.get("total_events", 0)
        latest = stats.get("latest_id", "")
        lines.append(
            f"+{total} events ingested | latest: {latest or 'N/A'} | healthcheck: "
        )

    return "\n".join(lines).rstrip() + "\n"


def render_nav_mermaid(state: dict) -> str:
    """MermaidのNav図（コードフェンス付きMarkdown）を返す。"""
    C = state.get("C", "")[:80]
    G = state.get("G", "")[:80]
    d = state.get("delta", "")[:80]
    return (
        "```mermaid\n"
        "flowchart LR\n"
        '  C["現在地 (C)"] --> route["推奨ルート"]\n'
        '  route --> G["目的地 (G)"]\n'
        '  C -.-> delta["差分 δ"]\n'
        '  decisions["主要決定"] --- route\n'
        '  risks["主要リスク"] -.-> route\n'
        f"%% C: {C}\n"
        f"%% G: {G}\n"
        f"%% δ: {d}\n"
        "```\n"
    )


def write_outputs(state: dict, out_docs: Path, out_diagrams: Path) -> tuple[Path, Path]:
    out_docs.mkdir(parents=True, exist_ok=True)
    out_diagrams.mkdir(parents=True, exist_ok=True)
    iso = _iso_date()

    md_path = out_docs / f"{iso}_digest.md"
    nav_md_path = out_diagrams / f"{iso}_nav.md"

    md_path.write_text(render_digest_md(state), encoding="utf-8")
    nav_md_path.write_text(render_nav_mermaid(state), encoding="utf-8")
    return md_path, nav_md_path


def _cli():
    p = argparse.ArgumentParser(
        description="Build Session Digest (markdown + mermaid) and update memory.json"
    )
    p.add_argument(
        "--input", "-i", default="-", help="Transcript file path (or '-' for STDIN)"
    )
    p.add_argument("--from-logs", help="Read from JSONL log file instead of --input")
    p.add_argument("--docs", default="docs/sessions", help="Output dir for digest md")
    p.add_argument(
        "--diagrams", default="diagrams/src", help="Output dir for mermaid md"
    )
    p.add_argument("--max-chars", type=int, default=400)
    args = p.parse_args()

    # --from-logs takes priority over --input
    if args.from_logs:
        text = extract_text_from_logs(args.from_logs)
    else:
        text = (
            sys.stdin.read()
            if args.input == "-"
            else open(args.input, "r", encoding="utf-8").read()
        )

    # 1) サマリ生成（≤400字）→ memory.json 先頭追記
    summary = summarize_last_session(text, args.max_chars)
    prepend_memory(summary)

    # 2) Digest骨格生成
    state = build_session_digest(text)

    # 3) 出力 (with stats if available)
    stats = get_stats()
    md_path = Path(args.docs) / f"{_iso_date()}_digest.md"
    nav_path = Path(args.diagrams) / f"{_iso_date()}_nav.md"

    Path(args.docs).mkdir(parents=True, exist_ok=True)
    Path(args.diagrams).mkdir(parents=True, exist_ok=True)

    md_path.write_text(render_digest_md(state, stats), encoding="utf-8")
    nav_path.write_text(render_nav_mermaid(state), encoding="utf-8")

    print(str(md_path))
    print(str(nav_path))


if __name__ == "__main__":
    _cli()
