#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a short conversation brief for hakone-e2 from "
            "canonical info_nodes/info_relations."
        )
    )
    parser.add_argument(
        "--nodes",
        default="data/hakone-e2/info_nodes_v1.json",
        help="Path to info_nodes JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--relations",
        default="data/hakone-e2/info_relations_v1.json",
        help="Path to info_relations JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=5,
        help="Max items to show per section for decision/gap/task (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. If omitted, prints to stdout.",
    )
    return parser.parse_args()


def load_json_array(path: Path, label: str) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"{label}: file not found: {path}")
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON in {path}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{label}: expected JSON array in {path}")
    return data


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[: max_len - 3] + "..."


def collect_items(
    nodes: Iterable[Dict[str, Any]],
    kind: str,
    max_items: int,
    *,
    subkind: str | None = None,
    id_contains: str | None = None,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for item in nodes:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "obsolete":
            continue
        if kind and item.get("kind") != kind:
            continue
        if subkind is not None and item.get("subkind") != subkind:
            continue
        if id_contains and id_contains not in str(item.get("id", "")):
            continue
        filtered.append(item)
    filtered.sort(key=lambda x: x.get("id", ""))
    if max_items >= 0:
        return filtered[:max_items]
    return filtered


def collect_gaps(
    nodes: Iterable[Dict[str, Any]],
    max_items: int,
) -> List[Dict[str, Any]]:
    gaps: List[Dict[str, Any]] = []
    for item in nodes:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "obsolete":
            continue
        is_gap = False
        if item.get("kind") == "fact" and item.get("subkind") == "gap":
            is_gap = True
        elif "gap" in str(item.get("id", "")):
            is_gap = True
        if is_gap:
            gaps.append(item)
    gaps.sort(key=lambda x: x.get("id", ""))
    if max_items >= 0:
        return gaps[:max_items]
    return gaps


def collect_supersedes(relations: Iterable[Dict[str, Any]]) -> List[str]:
    pairs: List[str] = []
    for rel in relations:
        if not isinstance(rel, dict):
            continue
        if rel.get("type") != "supersedes":
            continue
        from_id = rel.get("from")
        to_id = rel.get("to")
        if from_id and to_id:
            pairs.append(f"{from_id} -> {to_id}")
    pairs.sort()
    return pairs


def render_section(
    header: str,
    items: List[Dict[str, Any]],
    max_summary_len: int = 120,
) -> List[str]:
    lines = [f"## {header}"]
    if not items:
        lines.append("- (none)")
        return lines
    for item in items:
        item_id = str(item.get("id", "(missing id)"))
        title = str(item.get("title", "(no title)"))
        summary_raw = item.get("summary") or item.get("body") or ""
        summary = truncate(str(summary_raw), max_summary_len)
        lines.append(f"- {item_id} / {title} / {summary}")
    return lines


def render_supersedes(pairs: List[str]) -> List[str]:
    lines = ["## Supersedes"]
    if not pairs:
        lines.append("- (none)")
        return lines
    for pair in pairs:
        lines.append(f"- {pair}")
    return lines


def main() -> int:
    args = parse_args()
    nodes_path = Path(args.nodes)
    relations_path = Path(args.relations)

    try:
        nodes = load_json_array(nodes_path, "info_nodes")
        relations = load_json_array(relations_path, "info_relations")
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    decisions = collect_items(nodes, kind="decision", max_items=args.max_items)
    gaps = collect_gaps(nodes, max_items=args.max_items)
    tasks = collect_items(nodes, kind="task", max_items=args.max_items)
    supersedes = collect_supersedes(relations)

    lines: List[str] = ["# hakone-e2 Conversation Brief", ""]
    lines.extend(render_section("Decisions (active)", decisions))
    lines.append("")
    lines.extend(render_section("Gaps (active)", gaps))
    lines.append("")
    lines.extend(render_section("Tasks (active)", tasks))
    lines.append("")
    lines.extend(render_supersedes(supersedes))
    content = "\n".join(lines) + "\n"

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
