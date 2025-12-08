#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upsert aya_output info_nodes/info_relations into persistent files "
            "based on id."
        )
    )
    parser.add_argument(
        "--input",
        default="reports/hakone-e2/info_snapshot_v1_raw.json",
        help="Path to input snapshot JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--nodes",
        default="data/hakone-e2/info_nodes_v1.json",
        help="Path to destination info_nodes JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--relations",
        default="data/hakone-e2/info_relations_v1.json",
        help="Path to destination info_relations JSON (default: %(default)s)",
    )
    return parser.parse_args()


def load_json_array(path: Path, label: str) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON in {path}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{label}: expected a JSON array in {path}")
    return data


def load_input(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input: invalid JSON in {path}") from exc
    if not isinstance(data, dict):
        raise ValueError("Input: expected a JSON object at root")
    return data


def extract_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    if "aya_output" in data and isinstance(data["aya_output"], dict):
        return data["aya_output"]
    if isinstance(data, dict):
        return data
    raise ValueError(
        "Input: expected aya_output or root object with info_nodes/info_relations"
    )


def merge_by_id(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
    label: str,
) -> Tuple[int, int]:
    index = {}
    for idx, item in enumerate(existing):
        if isinstance(item, dict) and "id" in item:
            index[item["id"]] = idx
    added = 0
    updated = 0
    seen_updates = set()

    for item in incoming:
        if not isinstance(item, dict) or "id" not in item:
            print(f"{label}: skipping entry without id: {item}", file=sys.stderr)
            continue
        item_id = item["id"]
        if item_id in index:
            existing[index[item_id]] = item
            if item_id not in seen_updates:
                updated += 1
                seen_updates.add(item_id)
        else:
            existing.append(item)
            index[item_id] = len(existing) - 1
            added += 1
    return added, updated


def save_json_array(path: Path, data: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    nodes_path = Path(args.nodes)
    relations_path = Path(args.relations)

    try:
        input_data = load_input(input_path)
        payload = extract_payload(input_data)
        info_nodes = payload.get("info_nodes")
        info_relations = payload.get("info_relations")
    except (ValueError, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if info_nodes is None and info_relations is None:
        print("No info_nodes or info_relations found; nothing to do.")
        return 0

    if info_nodes is not None and not isinstance(info_nodes, list):
        print("info_nodes must be a list", file=sys.stderr)
        return 1
    if info_relations is not None and not isinstance(info_relations, list):
        print("info_relations must be a list", file=sys.stderr)
        return 1

    try:
        existing_nodes = load_json_array(nodes_path, "info_nodes")
        existing_relations = load_json_array(relations_path, "info_relations")
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    added_nodes = updated_nodes = 0
    if info_nodes is not None:
        added_nodes, updated_nodes = merge_by_id(
            existing_nodes, info_nodes, "info_nodes"
        )
        save_json_array(nodes_path, existing_nodes)

    added_relations = updated_relations = 0
    if info_relations is not None:
        added_relations, updated_relations = merge_by_id(
            existing_relations, info_relations, "info_relations"
        )
        save_json_array(relations_path, existing_relations)

    print(
        f"nodes: added {added_nodes}, updated {updated_nodes}, total {len(existing_nodes)}"
    )
    print(
        f"relations: added {added_relations}, updated {updated_relations}, total {len(existing_relations)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
