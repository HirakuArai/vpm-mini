#!/usr/bin/env python3
"""Validate understanding snapshot artefacts."""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent


def parse_md_sections(text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is None:
            continue
        sections[current].append(line.rstrip())
    return sections


def cleanup_items(lines: List[str]) -> List[str]:
    items: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return items


def expected_next_lines(entries: List[Dict[str, str]]) -> List[str]:
    if not entries:
        return ["(none)"]
    lines = []
    for entry in entries:
        title = entry.get("title", "")
        dod = entry.get("dod", "")
        reason = entry.get("reason", "")
        lines.append(f"{title} — DoD: {dod} (Reason: {reason})")
    return lines


def expected_constraints_lines(data: Dict[str, object]) -> Dict[str, str]:
    ruleset = data.get("constraints", {}).get("ruleset", {})
    branch = data.get("constraints", {}).get("branch", {})
    return {
        "Ruleset required": ", ".join(ruleset.get("required", [])) or "(none)",
        "Ruleset reported": ", ".join(ruleset.get("reported", [])) or "(none)",
        "Branch required": ", ".join(branch.get("required", [])) or "(none)",
        "Branch reported": ", ".join(branch.get("reported", [])) or "(none)",
    }


def ensure_required_vs_reported(
    data: Dict[str, object], errors: List[str], path: Path
) -> None:
    ruleset = data.get("constraints", {}).get("ruleset", {})
    required = set(ruleset.get("required", []))
    reported = set(ruleset.get("reported", []))
    missing = sorted(required - reported)
    if missing:
        errors.append(f"{path}: missing required ruleset checks: {', '.join(missing)}")
    # allow extras, but ensure duplicates removed
    if len(ruleset.get("reported", [])) != len(set(ruleset.get("reported", []))):
        errors.append(f"{path}: duplicate ruleset check names detected")

    branch = data.get("constraints", {}).get("branch", {})
    required_branch = set(branch.get("required", []))
    reported_branch = set(branch.get("reported", []))
    missing_branch = sorted(required_branch - reported_branch)
    if missing_branch:
        errors.append(
            f"{path}: missing required branch checks: {', '.join(missing_branch)}"
        )


def match_json_md(json_path: Path, md_path: Path) -> List[str]:
    errors: List[str] = []

    data = json.loads(json_path.read_text(encoding="utf-8"))
    sections = parse_md_sections(md_path.read_text(encoding="utf-8"))

    ensure_required_vs_reported(data, errors, json_path)

    # C section
    c_expected = data.get("c", []) or ["(none)"]
    c_actual = cleanup_items(sections.get("C", []))
    if c_actual != c_expected:
        errors.append(f"{md_path}: section C mismatch")

    # G section
    goals = data.get("g", {})
    g_expected = [
        f"Short: {goals.get('short', '')}",
        f"Mid: {goals.get('mid', '')}",
        f"Long: {goals.get('long', '')}",
    ]
    g_actual = cleanup_items(sections.get("G", []))
    if g_actual != g_expected:
        errors.append(f"{md_path}: section G mismatch")

    # δ section
    delta_expected = data.get("delta", []) or ["(none)"]
    delta_actual = cleanup_items(sections.get("δ", []))
    if delta_actual != delta_expected:
        errors.append(f"{md_path}: section δ mismatch")

    # Constraints
    constraint_lines = cleanup_items(sections.get("Constraints", []))
    exp_constraints = expected_constraints_lines(data)
    for key, value in exp_constraints.items():
        matches = [line for line in constraint_lines if line.startswith(f"{key}: ")]
        if not matches:
            errors.append(f"{md_path}: missing constraint line for '{key}'")
            continue
        actual_value = matches[0].split(":", 1)[1].strip()
        if actual_value != value:
            errors.append(f"{md_path}: constraint '{key}' mismatch")

    # Evidence
    evidence_expected = data.get("evidence", []) or ["(none)"]
    evidence_actual = cleanup_items(sections.get("Evidence", []))
    if evidence_actual != evidence_expected:
        errors.append(f"{md_path}: section Evidence mismatch")

    # Next
    next_expected = expected_next_lines(data.get("next", []))
    next_actual = cleanup_items(sections.get("Next (DoD/Reason)", []))
    if next_actual != next_expected:
        errors.append(f"{md_path}: section Next (DoD/Reason) mismatch")

    # Unknowns
    unknowns_dict = data.get("unknowns", {})
    if unknowns_dict:
        unknowns_expected = [f"{k}: {v}" for k, v in unknowns_dict.items()]
    else:
        unknowns_expected = ["(none)"]
    unknowns_actual = cleanup_items(sections.get("Unknowns", []))
    if unknowns_actual != unknowns_expected:
        errors.append(f"{md_path}: section Unknowns mismatch")

    # Conflicts
    conflicts_expected = data.get("conflicts", []) or ["(none)"]
    conflicts_actual = cleanup_items(sections.get("Conflicts / Mismatches", []))
    if conflicts_actual != conflicts_expected:
        errors.append(f"{md_path}: section Conflicts / Mismatches mismatch")

    # Sources
    sources_expected = data.get("sources", []) or ["(none)"]
    sources_actual = cleanup_items(sections.get("Sources", []))
    if sources_actual != sources_expected:
        errors.append(f"{md_path}: section Sources mismatch")

    return errors


def resolve_pairs(json_pattern: str, md_pattern: str) -> List[Tuple[Path, Path]]:
    json_files = sorted(glob.glob(str(ROOT / json_pattern)))
    md_files = sorted(glob.glob(str(ROOT / md_pattern)))
    pairs: List[Tuple[Path, Path]] = []
    md_lookup = {Path(path).stem: Path(path) for path in md_files}
    for jf in json_files:
        stem = Path(jf).stem
        md_path = md_lookup.get(stem)
        if md_path:
            pairs.append((Path(jf), md_path))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate understanding snapshot outputs"
    )
    parser.add_argument("--json", required=True, help="Glob for JSON files")
    parser.add_argument("--md", required=True, help="Glob for Markdown files")
    args = parser.parse_args()

    pairs = resolve_pairs(args.json, args.md)
    if not pairs:
        print("no matching snapshot artefacts found", file=sys.stderr)
        return 1

    all_errors: List[str] = []
    for json_path, md_path in pairs:
        errors = match_json_md(json_path, md_path)
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
