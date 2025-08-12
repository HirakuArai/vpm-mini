# vpm_mini/summary.py
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

KW = (
    "目的",
    "ゴール",
    "決定",
    "未決",
    "課題",
    "次",
    "リスク",
    "対応",
    "期限",
    "ブロッカー",
)


def _clean_text(txt: str) -> str:
    txt = re.sub(r"```.*?```", "", txt, flags=re.S)  # コードブロック除去
    txt = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", txt)  # MDリンク→テキスト
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _split_sentences_ja(txt: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[。．！!？\?])", txt) if s.strip()]


def _heuristic_summary(txt: str, max_chars: int) -> str:
    """LLMなしでもテストを通すフォールバック要約"""
    txt = _clean_text(txt)
    if len(txt) <= max_chars:
        return txt
    sents = _split_sentences_ja(txt)
    scored = []
    for i, s in enumerate(sents):
        sc = 1.0 if i == 0 else 0.0
        sc += sum(2.0 for k in KW if k in s)
        if len(s) < 12:
            sc -= 0.5
        scored.append((sc, i, s))
    ordered = [s for _, _, s in sorted(scored, key=lambda t: (-t[0], t[1]))]
    out = ""
    for s in ordered:
        if len(out) + len(s) <= max_chars:
            out += s
        else:
            out += s[: max_chars - len(out)]
            break
    return out.strip()[:max_chars] or txt[:max_chars]


def summarize_last_session(transcript: str, max_chars: int = 400) -> str:
    """≤400字の要約を返す（将来ここをLLM置換可）"""
    return _heuristic_summary(transcript, max_chars)


def prepend_memory(summary: str, memory_path: str = "memory.json") -> None:
    """memory.json（配列）に要約を**先頭**追加。壊れていれば .bak 退避して再生成。"""
    data: list = []
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            data = loaded if isinstance(loaded, list) else [str(loaded)]
        except Exception:
            try:
                os.rename(memory_path, memory_path + ".bak")
            except Exception:
                pass
            data = []
    s = summary.strip()
    if not s:
        return
    data.insert(0, s)
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- Session Digest 拡張用のダミーフック ----


def build_session_digest(transcript: str) -> dict:
    return {
        "type": "session_digest",
        "session_id": datetime.now(timezone.utc).isoformat(),
        "summary_ja_<=400chars": summarize_last_session(transcript, 400),
        "C": "",
        "G": "",
        "delta": "",
        "decisions": [],
        "open_questions": [],
        "todos": [],
        "risks": [],
        "evidence": [],
        "tags": [],
    }


# ---- CLI ----


def _cli():
    p = argparse.ArgumentParser(
        description="Generate <=400-char summary and prepend to memory.json"
    )
    p.add_argument(
        "--input", "-i", default="-", help="Transcript file path (or '-' for STDIN)"
    )
    p.add_argument("--max-chars", type=int, default=400)
    p.add_argument("--memory", default="memory.json")
    args = p.parse_args()

    text = (
        sys.stdin.read()
        if args.input == "-"
        else open(args.input, "r", encoding="utf-8").read()
    )
    summary = summarize_last_session(text, args.max_chars)
    prepend_memory(summary, args.memory)
    print(summary)


if __name__ == "__main__":
    _cli()
