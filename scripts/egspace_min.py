import json
import hashlib


def w(mins, role):
    roles = {"user": 1.0, "assistant": 0.7, "system": 0.5}
    return max(1.0, 60 / (mins + 1)) * roles.get(role, 0.8)


def embed(t):

    h = int(hashlib.sha256(t.encode()).hexdigest(), 16)
    return ((h % 2000) - 1000) / 1000.0


def load_mem(p="memory.json", n=50):
    try:
        mm = json.load(open(p, "r", encoding="utf-8"))
    except Exception:
        mm = []
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    out = []
    for m in mm[:n]:
        ts = m.get("created_at")
        try:
            from datetime import datetime, timezone

            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            mins = (now - dt).total_seconds() / 60
        except Exception:
            mins = 0
        out.append((mins, m.get("role", "user"), m.get("text", "")))
    return out


def goal(p="STATE/current_state.md"):
    try:
        s = open(p, "r", encoding="utf-8").read()
    except Exception:
        s = ""
    for line in reversed(s.splitlines()):
        if "GREEN" in line:
            return "GREEN"
    return "Goal"


def run():
    mem = load_mem()
    if not mem:
        return {"C": 0, "G": 0, "delta": 1, "d": 0}
    num = den = 0
    for mins, role, text in mem:
        num += w(mins, role) * embed(text)
        den += w(mins, role)
    C = num / den if den else 0
    G = embed(goal())
    d = G - C
    return {
        "C": round(C, 3),
        "G": round(G, 3),
        "delta": round(abs(d), 3),
        "d": round(d, 3),
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
