"""Grounded Q&A that consults SSOT artifacts and (optionally) LLM output."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from core.ask_json import ask_openai_json
from libs.ssot_scan import grep_snippets, verify_sources

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "STATE" / "current_state.md"
INVENTORY_PATH = REPO_ROOT / "inventory" / "inventory.csv"


def grounded_answer(question: str, use_ai: bool, budget: int = 2000) -> Dict[str, Any]:
    """
    Answer a question using SSOT snippets. Falls back to rule-based logic
    if ``use_ai`` is False or when the LLM path fails.
    """
    joined_text, snippets = grep_snippets(question, budget=budget)
    base_sources = _collect_sources(snippets)

    result = {
        "answer": "",
        "sources": base_sources.copy(),
        "confidence": 0.0,
        "unknown_fields": [],
    }

    if not use_ai:
        result["answer"] = _rule_based_answer(question)
        result["confidence"] = 0.4
        if not result["sources"]:
            result["sources"] = _default_sources()
        return result

    system_message = (
        "You answer strictly from the supplied SSOT snippets. "
        "If information is missing, respond with '不足' and include the missing fields "
        "in unknown_fields. "
        "Always return a JSON object with keys: "
        "answer (string), sources (array of repo-relative paths optionally with :Lx-Ly), "
        "confidence (float 0-1), unknown_fields (array of strings). "
        "If you must hypothesize, prefix with '仮説:'."
    )

    user_message = _build_user_prompt(question, joined_text)
    payload = ask_openai_json(system_message, user_message)
    if "error" in payload:
        logger.warning("LLM failed, falling back: %s", payload["error"])
        result["answer"] = f"AI回答失敗: {payload['error']}"
        result["sources"] = []
        result["confidence"] = 0.0
        result["unknown_fields"] = []
        return result

    normalized = _normalize_payload(payload, base_sources)
    result.update(normalized)

    ok, errors = verify_sources(result["sources"])
    if not ok:
        logger.warning("Source verification failed: %s", errors)
        result["answer"] = "不足: sources の検証に失敗しました。"
        result["sources"] = []
        result["confidence"] = min(float(result.get("confidence", 0.3)), 0.3)
        result["unknown_fields"] = errors

    return result


def _collect_sources(snippets: List[Dict[str, str]]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in snippets:
        path = item.get("path")
        if not path or path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return ordered


def _default_sources() -> List[str]:
    sources: List[str] = []
    if STATE_PATH.exists():
        sources.append(str(STATE_PATH.relative_to(REPO_ROOT)))
    if INVENTORY_PATH.exists():
        sources.append(str(INVENTORY_PATH.relative_to(REPO_ROOT)))
    return sources


def _build_user_prompt(question: str, joined_text: str) -> str:
    snippets_block = joined_text or "(抜粋が見つかりませんでした)"
    return f"質問:\n{question}\n\n" "SSOT抜粋:\n" f"{snippets_block}"


def _normalize_payload(
    payload: Dict[str, Any], base_sources: List[str]
) -> Dict[str, Any]:
    answer = payload.get("answer") if isinstance(payload.get("answer"), str) else ""
    sources = payload.get("sources")
    if isinstance(sources, list) and all(isinstance(item, str) for item in sources):
        normalized_sources = sources
    else:
        normalized_sources = []
    if not normalized_sources:
        normalized_sources = base_sources.copy()
    confidence = payload.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.0
    confidence_value = max(0.0, min(confidence_value, 1.0))

    unknown_fields = payload.get("unknown_fields")
    if not isinstance(unknown_fields, list):
        unknown_fields = []
    else:
        unknown_fields = [str(field) for field in unknown_fields]

    return {
        "answer": answer or "不足: 十分な情報が得られませんでした。",
        "sources": normalized_sources,
        "confidence": confidence_value,
        "unknown_fields": unknown_fields,
    }


def _rule_based_answer(question: str) -> str:
    state_text = _read_text(STATE_PATH)
    facts = _parse_state(state_text)
    lower_question = question.lower()

    if "phase" in lower_question:
        return (
            f"現在のPhaseは {facts['phase']} です。"
            f" 短期ゴール: {facts['short_goal']}。"
        )
    if "進捗" in question or "high" in lower_question:
        delta = facts["delta"]
        if delta:
            bullet = "\n".join(f"- {item}" for item in delta)
            return f"現状の差分δは以下です:\n{bullet}"
        return "STATE/current_state.md に δ が未記載です。更新してください。"
    if "残" in question or "todo" in lower_question:
        delta = facts["delta"]
        if delta:
            return f"未消化項目は {len(delta)} 件です。優先度順に対応してください。"
        return "未消化項目の記録が見つかりません。STATE を更新してください。"
    if "evidence" in lower_question or "証跡" in question:
        return "reports/ 以下に実行ログやスナップショットを保存し、sources にパスを残してください。"
    return "STATE/current_state.md と reports/ を確認し、SSOT を最新化してください。"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _parse_state(md: str) -> Dict[str, Any]:
    phase_match = re.search(r"phase=([^\s\"]+)", md)
    short_goal_match = re.search(r"P\d-[^\n]+", md)
    delta_section = re.search(r"##\s*δ[^#]*", md, re.S)
    deltas = []
    if delta_section:
        deltas = [
            line.strip()[2:].strip()
            for line in delta_section.group(0).splitlines()
            if line.strip().startswith("- ")
        ]
    return {
        "phase": phase_match.group(1) if phase_match else "不明",
        "short_goal": short_goal_match.group(0) if short_goal_match else "記載なし",
        "delta": deltas,
    }
