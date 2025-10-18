"""State drafting utilities driven by decision logs."""

from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml

try:  # pragma: no cover - optional dependency from Step1
    from core.ask_json import ask_openai_json
except Exception:  # pragma: no cover - fallback when LLM support is unavailable
    ask_openai_json = None  # type: ignore

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "STATE"


def draft_state(
    decisions_dir: str | Path = "reports/decisions",
    max_items: int = 10,
    use_ai: bool = False,
) -> Dict[str, Any]:
    """Assemble a STATE update draft based on decision log entries."""
    decisions_path = _resolve_decisions_dir(decisions_dir)
    entries = _load_decision_entries(decisions_path, max_items=max_items)
    today = _dt.datetime.now().strftime("%Y%m%d")
    target_rel = Path("STATE") / f"update_{today}.md"

    rule_body = _render_rule_based(entries)
    sources = _collect_sources(entries, decisions_path)

    if use_ai and ask_openai_json and entries:
        ai_result = _render_ai(entries)
        if ai_result:
            return {
                "path": str(target_rel),
                "body": ai_result["body"],
                "sources": ai_result.get("sources") or sources,
                "meta": {"ai_used": True},
            }

    return {
        "path": str(target_rel),
        "body": rule_body,
        "sources": sources,
        "meta": {"ai_used": False},
    }


def _resolve_decisions_dir(decisions_dir: str | Path) -> Path:
    decisions_path = Path(decisions_dir)
    if not decisions_path.is_absolute():
        decisions_path = REPO_ROOT / decisions_path
    return decisions_path


def _load_decision_entries(
    decisions_path: Path, max_items: int
) -> List[Dict[str, Any]]:
    if not decisions_path.exists():
        return []

    candidates = sorted(
        decisions_path.glob("D-*.yml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    entries: List[Dict[str, Any]] = []
    for path in candidates[:max_items]:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - corrupted file
            logger.warning("Failed to load decision file %s: %s", path, exc)
            continue
        if not isinstance(data, dict):
            logger.warning("Unsupported decision format in %s", path)
            continue
        entries.append(
            {
                "path": path,
                "id": data.get("id") or path.stem,
                "decision": data.get("decision") or "",
                "rationale": data.get("rationale") or "",
                "links": _normalise_links(data.get("links")),
            }
        )
    return entries


def _normalise_links(raw: Any) -> List[str]:
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Sequence):
        return [str(item) for item in raw]
    return []


def _render_rule_based(entries: Sequence[Dict[str, Any]]) -> str:
    lines: List[str] = ["# === STATE Update (Decisions sync) ===", ""]

    lines.append("## 概要")
    if entries:
        for entry in entries:
            bullet = (
                f"- **{entry['id']}**: {entry['decision'] or '（decision 未記載）'}"
            )
            rationale = entry.get("rationale")
            if rationale:
                bullet += f"\n  - 根拠: {rationale}"
            links = entry.get("links") or []
            if links:
                linked = ", ".join(links)
                bullet += f"\n  - Links: {linked}"
            lines.append(bullet)
    else:
        lines.append(
            "- Decision Log が空です。reports/decisions/ に D-*.yml を追加すると概要が表示されます。"
        )

    lines.extend(["", "## 反映内容"])
    if entries:
        for entry in entries:
            summary = (
                entry.get("decision")
                or entry.get("rationale")
                or "STATE への反映内容を検討してください。"
            )
            lines.append(f"- {entry['id']}: {summary}")
    else:
        lines.append("- 今回の Decision は未登録のため、C/G/δ の更新候補はありません。")

    lines.extend(["", "## DoD"])
    lines.append("- STATE/current_state.md を更新し、C/G/δ に決定事項を反映する。")
    lines.append("- 更新内容の証跡（reports/、PR、ダッシュボードなど）を添付する。")
    lines.append("- Decision Log と STATE の差異をレビューで確認する。")

    lines.extend(["", "## Sources"])
    source_lines = []
    for entry in entries:
        rel = _relative_to_repo(entry["path"])
        links = entry.get("links") or []
        if links:
            source_lines.append(f"- {rel} (links: {', '.join(links)})")
        else:
            source_lines.append(f"- {rel}")
    source_lines.append("- STATE/current_state.md")
    if not entries:
        source_lines.append("- （Decision Log 未登録）")
    lines.extend(source_lines)

    return "\n".join(lines).strip() + "\n"


def _render_ai(entries: Sequence[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not ask_openai_json:
        return None

    system_message = (
        "You are drafting a STATE update using only the supplied decision log entries. "
        "Output valid Markdown with sections: 概要, 反映内容, DoD, Sources. "
        "List concrete sources using repo-relative paths and any provided links. "
        "If information is missing, use '仮説:' to mark assumptions. "
        "Respond as JSON with keys 'body' (markdown string) and 'sources' (array of strings)."
    )

    decision_snippets = []
    for entry in entries:
        links = entry.get("links") or []
        snippet = {
            "id": entry["id"],
            "decision": entry["decision"],
            "rationale": entry["rationale"],
            "links": links,
            "path": _relative_to_repo(entry["path"]),
        }
        decision_snippets.append(snippet)

    user_message = (
        "以下は最新の Decision Log です。"
        "内容をもとに STATE/update の Markdown を作成してください。\n\n"
        f"{yaml.safe_dump(decision_snippets, allow_unicode=True)}"
    )

    payload = ask_openai_json(system_message, user_message)  # type: ignore[arg-type]
    if not isinstance(payload, dict):
        return None
    if payload.get("error"):
        logger.warning("LLM draft failed: %s", payload["error"])
        return None
    body = payload.get("body")
    if not isinstance(body, str):
        logger.warning("LLM response missing body")
        return None
    sources = payload.get("sources")
    if isinstance(sources, list) and all(isinstance(item, str) for item in sources):
        source_list = sources
    else:
        source_list = []
    return {"body": body.strip() + "\n", "sources": source_list}


def _collect_sources(
    entries: Sequence[Dict[str, Any]], decisions_path: Path
) -> List[str]:
    sources = [_relative_to_repo(entry["path"]) for entry in entries]
    sources.append(_relative_to_repo(STATE_DIR / "current_state.md"))
    if not entries and decisions_path.exists():
        sources.append(_relative_to_repo(decisions_path))
    return sources


def _relative_to_repo(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
