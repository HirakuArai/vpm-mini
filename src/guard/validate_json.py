"""Validation helpers for Step 1-3 artifacts (answer, plan, state)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from libs.ssot_scan import verify_sources

REPO_ROOT = Path(__file__).resolve().parents[2]


def validate_answer(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(payload, dict):
        return False, ["payload must be an object"]

    answer = payload.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        errs.append("answer must be a non-empty string")

    sources = payload.get("sources")
    if not isinstance(sources, list) or not all(isinstance(s, str) for s in sources):
        errs.append("sources must be a list of strings")
    elif not sources:
        errs.append("sources must not be empty")

    confidence = payload.get("confidence")
    try:
        confidence_value = float(confidence)
        if confidence_value < 0 or confidence_value > 1:
            errs.append("confidence must be between 0 and 1")
    except (TypeError, ValueError):
        errs.append("confidence must be a number")

    unknown_fields = payload.get("unknown_fields")
    if not isinstance(unknown_fields, list):
        errs.append("unknown_fields must be a list")

    if not errs and sources:
        ok, source_errs = verify_sources(sources)
        if not ok:
            errs.extend(source_errs)

    return not errs, errs


def validate_plan(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(payload, dict):
        return False, ["payload must be an object"]

    next_actions = payload.get("next_actions")
    if not isinstance(next_actions, list):
        return False, ["next_actions must be a list"]

    all_sources: List[str] = []
    for idx, action in enumerate(next_actions):
        if not isinstance(action, dict):
            errs.append(f"next_actions[{idx}] must be an object")
            continue
        for key in ("id", "title", "owner"):
            if not isinstance(action.get(key), str) or not action.get(key):
                errs.append(f"next_actions[{idx}].{key} must be a non-empty string")
        priority = action.get("priority")
        if not isinstance(priority, int):
            errs.append(f"next_actions[{idx}].priority must be an integer")
        dod = action.get("DoD")
        if (
            not isinstance(dod, list)
            or not dod
            or not all(isinstance(item, str) for item in dod)
        ):
            errs.append(f"next_actions[{idx}].DoD must be a non-empty list of strings")
        sources = action.get("sources")
        if (
            not isinstance(sources, list)
            or not sources
            or not all(isinstance(src, str) for src in sources)
        ):
            errs.append(
                f"next_actions[{idx}].sources must be a non-empty list of strings"
            )
        else:
            all_sources.extend(sources)

    if not errs and all_sources:
        ok, source_errs = verify_sources(all_sources)
        if not ok:
            errs.extend(source_errs)

    return not errs, errs


def validate_state_md(md_text: str) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(md_text, str):
        return False, ["state content must be a string"]

    lines = [line.rstrip() for line in md_text.splitlines()]
    if not lines or not lines[0].startswith("# === STATE Update"):
        errs.append("title '# === STATE Update...' is missing")

    sources_section = False
    sources: List[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped.startswith("##") and "sources" in stripped:
            sources_section = True
            continue
        if sources_section and line.startswith("-"):
            src = line.lstrip("- ")
            if src:
                sources.append(src.split("(")[0].strip())
        elif sources_section and line.startswith("##"):
            break

    if not sources_section:
        errs.append("Sources section is missing")
    elif not sources:
        errs.append("Sources section must list at least one entry")
    else:
        ok, source_errs = verify_sources(sources)
        if not ok:
            errs.extend(source_errs)

    return not errs, errs


def load_json(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
