"""Lightweight wrapper for JSON-constrained OpenAI chat completions."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def ask_openai_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Call the OpenAI chat API requesting a JSON object response.

    Errors are caught and converted into {"error": "..."} so that callers can
    perform a graceful fallback without raising.
    """
    client = _resolve_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception as exc:  # pragma: no cover - network failure path
        logger.warning("OpenAI JSON completion failed: %s", exc)
        return {"error": f"{exc.__class__.__name__}: {exc}"}

    message = response.choices[0].message if response.choices else None
    payload = getattr(message, "content", None) or "{}"
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to decode JSON payload: %s", exc)
        return {"error": f"JSONDecodeError: {exc}"}


def _resolve_client():
    try:
        from core import get_openai_client  # type: ignore
    except Exception as exc:  # pragma: no cover - import edge case
        logger.warning("Falling back to direct OpenAI client: %s", exc)
        from openai import OpenAI

        return OpenAI()
    else:
        return get_openai_client()
