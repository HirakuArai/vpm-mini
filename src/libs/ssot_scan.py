"""
Utilities for scanning SSOT (single source of truth) assets to support
grounded question answering.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = REPO_ROOT / "STATE" / "current_state.md"
INVENTORY_PATH = REPO_ROOT / "inventory" / "inventory.csv"
DECISIONS_DIR = REPO_ROOT / "reports" / "decisions"
REPORTS_DIR = REPO_ROOT / "reports"

MAX_REPORT_FILES = 10
REPORT_SIZE_LIMIT = 128 * 1024  # bytes

SOURCE_PATTERN = re.compile(
    r"^(?P<path>[^:]+)(?::L(?P<start>\d+)(?:-L?(?P<end>\d+))?)?$"
)


def list_ssot_targets() -> List[Path]:
    """Return SSOT files in priority order if they exist."""
    targets: List[Path] = []

    if STATE_PATH.exists():
        targets.append(STATE_PATH)

    if DECISIONS_DIR.exists():
        decision_files = sorted(
            DECISIONS_DIR.glob("D-*.yml"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        targets.extend(decision_files)

    if REPORTS_DIR.exists():
        report_files: List[Path] = []
        for candidate in sorted(
            REPORTS_DIR.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            if len(report_files) >= MAX_REPORT_FILES:
                break
            try:
                size = candidate.stat().st_size
            except OSError as exc:
                logger.warning("Unable to inspect %s: %s", candidate, exc)
                continue
            if size > REPORT_SIZE_LIMIT:
                logger.warning(
                    "Skipping %s (size %s bytes exceeds limit)",
                    candidate,
                    size,
                )
                continue
            report_files.append(candidate)
        targets.extend(report_files)

    if INVENTORY_PATH.exists():
        targets.append(INVENTORY_PATH)

    return targets


def grep_snippets(
    question: str, budget: int = 2000
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Collect small snippets from SSOT files using a rough relevance heuristic.

    Returns:
        joined text (<= budget chars) and a list of {path, snippet}.
    """

    def remaining_budget(current: int) -> int:
        return max(budget - current, 0)

    terms = [t.lower() for t in re.split(r"\W+", question) if t]
    snippets: List[Dict[str, str]] = []
    joined_parts: List[str] = []
    used = 0

    category_budgets = [
        ("state", 1200),
        ("decisions", 400),
        ("reports", 300),
        ("inventory", 100),
    ]

    targets = list_ssot_targets()
    by_category: Dict[str, List[Path]] = {
        "state": [],
        "decisions": [],
        "reports": [],
        "inventory": [],
    }
    for path in targets:
        if path == STATE_PATH:
            by_category["state"].append(path)
        elif DECISIONS_DIR in path.parents:
            by_category["decisions"].append(path)
        elif path.parent == REPORTS_DIR:
            by_category["reports"].append(path)
        elif path == INVENTORY_PATH:
            by_category["inventory"].append(path)

    for category, category_budget in category_budgets:
        paths = by_category.get(category, [])
        if not paths:
            continue

        category_remaining = min(category_budget, remaining_budget(used))
        if category_remaining <= 0:
            break

        for idx, path in enumerate(paths):
            if category_remaining <= 0 or remaining_budget(used) <= 0:
                break
            slots_left = len(paths) - idx
            share = max(category_remaining // slots_left, 1)
            allowed = min(share, remaining_budget(used))
            snippet = _extract_snippet(path, terms, allowed)
            if not snippet:
                continue
            rel_path = str(path.relative_to(REPO_ROOT))
            snippets.append({"path": rel_path, "snippet": snippet})
            joined_parts.append(f"[{rel_path}]\n{snippet}")
            snippet_len = len(snippet)
            used += snippet_len
            category_remaining -= min(snippet_len, share)
            if used >= budget:
                break
        if used >= budget:
            break

    joined_text = "\n\n".join(joined_parts)
    return joined_text, snippets


def verify_sources(sources: Iterable[str]) -> Tuple[bool, List[str]]:
    """Validate that each source refers to an existing file and optional line range."""
    errors: List[str] = []
    if isinstance(sources, (str, bytes)):
        return False, ["sources must be a list of strings"]
    if not isinstance(sources, Iterable):
        return False, ["sources must be iterable"]

    line_cache: Dict[Path, int] = {}

    for raw in sources:
        if not isinstance(raw, str):
            errors.append("source must be a string")
            continue
        source = raw.strip()
        if not source:
            errors.append("source may not be empty")
            continue
        match = SOURCE_PATTERN.match(source)
        if not match:
            errors.append(f"invalid source format: {source}")
            continue
        rel_part = match.group("path")
        resolved = (REPO_ROOT / rel_part).resolve()
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            errors.append(f"source outside repository: {source}")
            continue
        if not resolved.exists():
            errors.append(f"missing source file: {source}")
            continue
        start_str = match.group("start")
        end_str = match.group("end")
        if start_str:
            start = int(start_str)
            end = int(end_str) if end_str else start
            if start < 1 or end < start:
                errors.append(f"invalid line range in source: {source}")
                continue
            total_lines = line_cache.get(resolved)
            if total_lines is None:
                try:
                    with resolved.open("r", encoding="utf-8", errors="ignore") as fh:
                        total_lines = sum(1 for _ in fh)
                except OSError as exc:
                    errors.append(f"unable to read {source}: {exc}")
                    continue
                line_cache[resolved] = total_lines
            if end > total_lines:
                errors.append(f"line range out of bounds: {source}")

    return len(errors) == 0, errors


def _extract_snippet(path: Path, terms: List[str], budget: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return ""

    if not text:
        return ""

    budget = max(budget, 0)
    if budget == 0:
        return ""

    lower_text = text.lower()
    snippet = ""
    for term in terms:
        idx = lower_text.find(term)
        if idx != -1:
            start = max(idx - budget // 4, 0)
            snippet = text[start : start + budget]
            break

    if not snippet:
        snippet = text[:budget]

    return snippet.strip()
