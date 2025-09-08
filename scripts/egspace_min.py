import json
import hashlib
from datetime import datetime, timezone


def _w(mins, role):
    roles = {"user": 1.0, "assistant": 0.7, "system": 0.5}
    return max(1.0, 60.0 / (mins + 1.0)) * roles.get(role, 0.8)


def _embed(text):
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    return ((h % 2000) - 1000) / 1000.0  # -1..+1 の擬似1次元


def _load_memory(path="memory.json", limit=50):
    try:
        with open(path, "r", encoding="utf-8") as f:
            mm = json.load(f)
        if not isinstance(mm, list):
            mm = []
    except Exception:
        mm = []

    now = datetime.now(timezone.utc)
    out = []
    for m in mm[:limit]:
        # Handle string entries (malformed data)
        if isinstance(m, str):
            out.append((0.0, "user", m[:200]))  # Truncate long strings
            continue

        if not isinstance(m, dict):
            continue

        txt = (m.get("text") or "").strip()
        role = (m.get("role") or "user").strip().lower()
        ts = (m.get("created_at") or "").strip()
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            mins = max(0.0, (now - dt).total_seconds() / 60.0)
        except Exception:
            mins = 0.0
        out.append((mins, role, txt))
    return out


def _goal_from_state(path="STATE/current_state.md"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            s = f.read()
    except Exception:
        s = ""
    for line in reversed(s.splitlines()):
        if "GREEN" in line:
            return "GREEN"
    return "Goal"


def compute():
    mem = _load_memory()
    if not mem:
        return {"C": 0.0, "G": 0.0, "delta": 1.0, "d": 0.0, "note": "no-memory"}
    num = den = 0.0
    for mins, role, txt in mem:
        num += _w(mins, role) * _embed(txt or "EMPTY")
        den += _w(mins, role)
    C = (num / den) if den else 0.0
    G = _embed(_goal_from_state())
    d = G - C
    return {
        "C": round(C, 3),
        "G": round(G, 3),
        "delta": round(abs(d), 3),
        "d": round(d, 3),
    }


if __name__ == "__main__":
    # 絶対に例外で落とさず、JSONを返して exit 0
    try:
        out = compute()
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        print(
            json.dumps(
                {"C": 0.0, "G": 0.0, "delta": 1.0, "d": 0.0, "error": str(e)},
                ensure_ascii=False,
            )
        )
    raise SystemExit(0)
