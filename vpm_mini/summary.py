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

SECTION_KEYS = {
    "C": ("現状", "現在地", "C"),
    "G": ("目的", "ゴール", "G"),
    "delta": ("差分", "δ", "デルタ"),
    "decisions": ("決定", "合意", "方針"),
    "open_questions": ("未決", "Open", "懸案"),
    "todos": ("TODO", "次", "対応"),
    "risks": ("リスク", "懸念"),
}

_bullet = re.compile(r"^[\-\*・]\s*(.+)$")
_hdr = re.compile(r"^\s{0,3}(#{1,6}|[*]{1}|\d+\.)\s*([^#\n]+)$")


def _collect_lines(text: str, keys: tuple[str, ...]) -> list[str]:
    """見出しやキーワードに続く箇条書きを抽出（簡易）。"""
    lines = text.splitlines()
    picked: list[str] = []
    capture = False
    for ln in lines:
        if any(k in ln for k in keys):
            capture = True
            continue
        if capture:
            m = _bullet.match(ln.strip())
            if m:
                picked.append(m.group(1).strip())
            else:
                # 箇条書きが途切れたら終了
                if ln.strip() and _hdr.match(ln):
                    break
    return picked


def _first_paragraph(text: str, keys: tuple[str, ...]) -> str:
    """キーワードを含む行以降の最初の段落をざっくり返す。"""
    lines = text.splitlines()
    buf: list[str] = []
    capture = False
    for ln in lines:
        if any(k in ln for k in keys):
            capture = True
            continue
        if capture:
            if ln.strip() == "":
                if buf:
                    break
                else:
                    continue
            buf.append(ln.strip())
    return " ".join(buf).strip()


def build_session_digest(transcript: str) -> dict:
    """
    軽量抽出で Session Digest の骨格を生成。
    - summary: ≤400字（既存関数）
    - C/G/δ: キーに続く段落の先頭
    - decisions/open/todos/risks: 箇条書き抽出
    - evidence/tags: MVPでは空 or 簡易推定
    """
    summary = summarize_last_session(transcript, 400)

    C = _first_paragraph(transcript, SECTION_KEYS["C"]) or ""
    G = _first_paragraph(transcript, SECTION_KEYS["G"]) or ""
    delta = _first_paragraph(transcript, SECTION_KEYS["delta"]) or ""

    decisions = _collect_lines(transcript, SECTION_KEYS["decisions"]) or []
    open_q = _collect_lines(transcript, SECTION_KEYS["open_questions"]) or []
    todos = _collect_lines(transcript, SECTION_KEYS["todos"]) or []
    risks = _collect_lines(transcript, SECTION_KEYS["risks"]) or []

    # 参照IDはMVPでは未付与。将来 `E:YYYY-MM-DD#n` を割り当て。
    return {
        "type": "session_digest",
        "session_id": datetime.now(timezone.utc).isoformat(),
        "summary_ja_<=400chars": summary,
        "C": C,
        "G": G,
        "delta": delta,
        "decisions": decisions,
        "open_questions": open_q,
        "todos": todos,
        "risks": risks,
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
