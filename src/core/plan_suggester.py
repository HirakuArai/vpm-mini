"""Plan suggester that assembles prioritized next actions from SSOT inputs."""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from core.ask_json import ask_openai_json
from libs.ssot_scan import verify_sources

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPO_ROOT / "inventory" / "inventory.csv"
STATE_PATH = REPO_ROOT / "STATE" / "current_state.md"
DECISIONS_DIR = REPO_ROOT / "reports" / "decisions"

MAX_DECISIONS = 10
AI_BUDGET_CHARS = 2000


CRITICALITY_SCORE = {"H": 3, "M": 2, "L": 1}
RISK_SCORE = {"HIGH": 3, "MED": 2, "MEDIUM": 2, "LOW": 1}
EFFORT_SCORE = {"S": 3, "M": 2, "L": 1}

DOD_MAP = {
    "rehost": [
        "件数一致 ±0.1%",
        "主要KPI差分 <= 0.5%",
        "BIスクショ差分 OK",
    ],
    "refactor": [
        "E2Eジョブ成功",
        "テーブル整合性確認",
        "ロールバック手順確認",
    ],
    "replace": [
        "ダッシュボードスクショ差分 OK",
        "主要集計一致",
        "権限設定完了",
    ],
    "retire": [
        "オーナ承認取得",
        "アクセスログ 0 を確認",
        "依存なし確認",
    ],
    "retain": [
        "現行手順の維持計画を明文化",
        "監視カバレッジを確認",
        "次回見直し日を設定",
    ],
}


@dataclass
class InventoryEntry:
    asset_id: str
    kind: str
    name: str
    owner: str
    criticality: str
    status: str
    due_date: Optional[dt.date]
    est_effort: str
    risk: str
    target_option: str
    links: List[str]
    score: float


def suggest_plan(use_ai: bool = False, limit: int = 5) -> Dict[str, Any]:
    """Return prioritized next actions based on inventory/STATE/decisions."""

    inventory = _load_inventory()
    decisions = _load_decisions()
    short_goal = _extract_short_goal()

    rule_plan = _build_rule_plan(inventory, decisions, short_goal, limit)

    if not use_ai:
        return rule_plan

    ai_plan = _try_ai_plan(inventory, decisions, short_goal, limit)
    if ai_plan is None:
        return rule_plan

    flat_sources: List[str] = []
    for action in ai_plan.get("next_actions", []):
        action_sources = action.get("sources") if isinstance(action, dict) else None
        if isinstance(action_sources, list):
            flat_sources.extend(action_sources)
    if flat_sources:
        ok, errors = verify_sources(flat_sources)
        if not ok:
            logger.warning("AI plan sources invalid: %s", errors)
            return rule_plan

    return ai_plan


def _load_inventory() -> List[InventoryEntry]:
    if not INVENTORY_PATH.exists():
        return []

    entries: List[InventoryEntry] = []
    with INVENTORY_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        today = dt.date.today()
        for row in reader:
            asset_id = (row.get("asset_id") or "").strip()
            if not asset_id or asset_id.startswith("SAMPLE-"):
                continue
            due_date = _parse_date(row.get("due_date") or "")
            est_effort = (row.get("est_effort") or "M").upper()
            risk = (row.get("risk") or "MED").upper()
            target_option = (row.get("target_option") or row.get("kind") or "").lower()
            score = _compute_score(
                criticality=row.get("criticality"),
                due_date=due_date,
                est_effort=est_effort,
                risk=risk,
                today=today,
            )
            links_raw = row.get("links") or ""
            links = [link.strip() for link in links_raw.split(";") if link.strip()]
            entries.append(
                InventoryEntry(
                    asset_id=asset_id,
                    kind=row.get("kind") or "",
                    name=row.get("name") or asset_id,
                    owner=row.get("owner") or "未設定",
                    criticality=(row.get("criticality") or "M").upper(),
                    status=row.get("status") or "",
                    due_date=due_date,
                    est_effort=est_effort,
                    risk=risk,
                    target_option=target_option,
                    links=links,
                    score=score,
                )
            )
    entries.sort(key=lambda item: item.score, reverse=True)
    return entries


def _compute_score(
    *,
    criticality: Optional[str],
    due_date: Optional[dt.date],
    est_effort: str,
    risk: str,
    today: dt.date,
) -> float:
    score = float(CRITICALITY_SCORE.get((criticality or "M").upper(), 2))

    if due_date:
        days_until = (due_date - today).days
        if days_until <= 0:
            deadline_score = 5
        elif days_until <= 7:
            deadline_score = 4
        elif days_until <= 30:
            deadline_score = 3
        elif days_until <= 90:
            deadline_score = 2
        else:
            deadline_score = 1
        score += deadline_score

    effort_score = EFFORT_SCORE.get(est_effort.upper(), 2)
    score += max(0, 4 - effort_score)

    score += RISK_SCORE.get(risk.upper(), 2)
    return score


def _parse_date(raw: str) -> Optional[dt.date]:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        return None


def _load_decisions(max_items: int = MAX_DECISIONS) -> List[Dict[str, Any]]:
    if not DECISIONS_DIR.exists():
        return []
    files = sorted(
        DECISIONS_DIR.glob("D-*.yml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:max_items]
    decisions: List[Dict[str, Any]] = []
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to load decision %s: %s", path, exc)
            continue
        if not isinstance(data, dict):
            continue
        item = {
            "id": data.get("id") or path.stem,
            "decision": data.get("decision"),
            "rationale": data.get("rationale"),
            "links": data.get("links") or [],
            "path": str(path.relative_to(REPO_ROOT)),
        }
        decisions.append(item)
    return decisions


def _extract_short_goal() -> str:
    if not STATE_PATH.exists():
        return ""
    text = STATE_PATH.read_text(encoding="utf-8")
    for marker in ["短期ゴール", "short_goal", "短期ゴール:"]:
        idx = text.find(marker)
        if idx != -1:
            snippet = text[idx:].splitlines()
            if snippet:
                line = snippet[0]
                if ":" in line:
                    return line.split(":", 1)[1].strip()
                return line.strip()
    return ""


def _build_rule_plan(
    inventory: Sequence[InventoryEntry],
    decisions: Sequence[Dict[str, Any]],
    short_goal: str,
    limit: int,
) -> Dict[str, Any]:
    actions: List[Dict[str, Any]] = []
    decision_sources = [item["path"] for item in decisions]
    decision_links: List[str] = []
    for item in decisions:
        links = item.get("links") or []
        if isinstance(links, list):
            for link in links:
                if link not in decision_links:
                    decision_links.append(link)

    for priority, entry in enumerate(inventory[:limit], start=1):
        category = _determine_category(entry)
        dod_items = DOD_MAP.get(
            category, DOD_MAP.get("retain" if category == "retain" else "refactor", [])
        )
        action = {
            "id": entry.asset_id,
            "title": _compose_title(entry, category),
            "priority": priority,
            "DoD": dod_items,
            "owner": entry.owner,
            "due": entry.due_date.isoformat() if entry.due_date else "",
            "links": entry.links or decision_links,
            "sources": _collect_sources(decision_sources),
        }
        actions.append(action)

    return {
        "next_actions": actions,
        "short_goal": short_goal,
    }


def _determine_category(entry: InventoryEntry) -> str:
    option = entry.target_option.lower()
    if option in DOD_MAP:
        return option
    kind = entry.kind.lower()
    for key in DOD_MAP:
        if key in option or key in kind:
            return key
    if "retain" in option or "retain" in kind:
        return "retain"
    return "refactor"


def _compose_title(entry: InventoryEntry, category: str) -> str:
    prefix = category.capitalize()
    name = entry.name or entry.asset_id
    return f"{prefix}: {name}"


def _collect_sources(decision_sources: Sequence[str]) -> List[str]:
    sources = ["inventory/inventory.csv"]
    sources.extend(decision_sources[:1])
    sources.append("STATE/current_state.md")
    return sorted(set(sources))


def _try_ai_plan(
    inventory: Sequence[InventoryEntry],
    decisions: Sequence[Dict[str, Any]],
    short_goal: str,
    limit: int,
) -> Optional[Dict[str, Any]]:
    try:
        payload = _request_ai_plan(inventory, decisions, short_goal)
    except Exception as exc:  # pragma: no cover - network failure path
        logger.warning("AI plan request failed: %s", exc)
        return None

    if not isinstance(payload, dict) or payload.get("error"):
        logger.warning("AI plan returned error: %s", payload.get("error"))
        return None

    normalized = _normalize_ai_plan(payload, limit)
    if not normalized["next_actions"]:
        return normalized

    for action in normalized["next_actions"]:
        sources = action.get("sources")
        if not isinstance(sources, list):
            return None
        ok, errors = verify_sources(sources)
        if not ok:
            logger.warning("AI plan action sources invalid: %s", errors)
            return None

    return normalized


def _request_ai_plan(
    inventory: Sequence[InventoryEntry],
    decisions: Sequence[Dict[str, Any]],
    short_goal: str,
) -> Dict[str, Any]:
    if ask_openai_json is None:
        raise RuntimeError("ask_openai_json is unavailable")

    system_prompt = (
        "You receive SSOT snippets (inventory, STATE, decision logs). "
        "Return JSON with keys next_actions (array of {id,title,priority,DoD,owner,due,links,sources}) "
        "and short_goal. Use only the provided data. "
        "If you hypothesize, prefix with '仮説:'. "
        "Priority must consider criticality, deadline, effort, and risk. "
        "sources must list repo-relative paths explicitly."
    )

    inventory_snippet = [
        {
            "asset_id": entry.asset_id,
            "kind": entry.kind,
            "owner": entry.owner,
            "criticality": entry.criticality,
            "due_date": entry.due_date.isoformat() if entry.due_date else "",
            "est_effort": entry.est_effort,
            "risk": entry.risk,
            "target_option": entry.target_option,
        }
        for entry in inventory[:50]
    ]

    decision_snippet = [
        {
            key: value
            for key, value in item.items()
            if key in {"id", "decision", "rationale", "links", "path"}
        }
        for item in decisions
    ]

    state_text = ""
    if STATE_PATH.exists():
        state_text = STATE_PATH.read_text(encoding="utf-8")[:400]

    user_payload = {
        "short_goal": short_goal,
        "state_excerpt": state_text,
        "inventory": inventory_snippet,
        "decisions": decision_snippet,
    }
    user_message = json.dumps(user_payload, ensure_ascii=False)
    if len(user_message) > AI_BUDGET_CHARS:
        user_message = user_message[:AI_BUDGET_CHARS]

    return ask_openai_json(system_prompt, user_message)


def _normalize_ai_plan(payload: Dict[str, Any], limit: int) -> Dict[str, Any]:
    next_actions = payload.get("next_actions")
    if not isinstance(next_actions, list):
        next_actions = []
    normalized_actions: List[Dict[str, Any]] = []
    for idx, raw in enumerate(next_actions[:limit], start=1):
        if not isinstance(raw, dict):
            continue
        action = {
            "id": str(raw.get("id") or f"AI-{idx}"),
            "title": str(raw.get("title") or raw.get("id") or f"提案 {idx}"),
            "priority": _to_int(raw.get("priority"), idx),
            "DoD": _ensure_string_list(raw.get("DoD")),
            "owner": str(raw.get("owner") or "未設定"),
            "due": str(raw.get("due") or ""),
            "links": _ensure_string_list(raw.get("links")),
            "sources": _ensure_string_list(raw.get("sources"))
            or ["inventory/inventory.csv"],
        }
        normalized_actions.append(action)

    short_goal = payload.get("short_goal")
    if not isinstance(short_goal, str):
        short_goal = ""

    return {
        "next_actions": normalized_actions,
        "short_goal": short_goal,
    }


def _ensure_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str) and value:
        return [value]
    return []


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)
