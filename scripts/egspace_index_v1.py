import os
import json
import glob
import hashlib
import time
import numpy as np
from datetime import datetime, timezone
import psycopg

EMB_DIM = 384


def try_sbert():
    try:
        from sentence_transformers import SentenceTransformer

        m = SentenceTransformer("all-MiniLM-L6-v2")

        def emb(texts):
            X = m.encode(texts, normalize_embeddings=True)
            return np.asarray(X, dtype=np.float32)

        return emb, "sbert:all-MiniLM-L6-v2"
    except Exception:
        return None, None


def emb_hash(texts):
    vecs = []
    for t in texts:
        rng = np.random.default_rng(
            int(hashlib.sha256(t.encode()).hexdigest(), 16) % (1 << 32)
        )
        v = rng.standard_normal(EMB_DIM).astype(np.float32)
        v /= np.linalg.norm(v) + 1e-9
        vecs.append(v)
    return np.stack(vecs, 0), "hashing-fallback"


def load_corpus():
    items = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # memory.json
    try:
        mem = json.load(open("memory.json", "r", encoding="utf-8"))
        for i, m in enumerate(mem[:200]):
            txt = (m.get("text") or "").strip()
            if txt:
                items.append(("memory", f"memory[{i}]", now, txt))
    except Exception:
        ...
    # STATE
    goal = "Goal"
    try:
        st = open("STATE/current_state.md", "r", encoding="utf-8").read()
        items.append(("state", "STATE/current_state.md", now, st))
        for line in reversed(st.splitlines()):
            if "GREEN" in line:
                goal = line.strip()
                break
    except Exception:
        ...
    # reports（最新100件程度）
    for p in sorted(glob.glob("reports/*.md"))[-100:]:
        try:
            items.append(("report", p, now, open(p, "r", encoding="utf-8").read()))
        except Exception:
            ...
    return items, goal


def upsert(conn, items, embf):
    with conn.cursor() as cur:
        cur.execute(
            f"""
CREATE TABLE IF NOT EXISTS items(
  id bigserial PRIMARY KEY,
  kind text, path text, ts timestamptz,
  txt text,
  emb vector({EMB_DIM}),
  UNIQUE(kind,path)
);"""
        )
        texts = [t for *_, t in items]
        if not texts:
            return 0
        V = embf(texts)
        for (kind, path, ts, txt), v in zip(items, V):
            cur.execute(
                """INSERT INTO items(kind,path,ts,txt,emb)
                           VALUES(%s,%s,%s,%s,%s)
                           ON CONFLICT(kind,path) DO UPDATE
                           SET ts=EXCLUDED.ts, txt=EXCLUDED.txt, emb=EXCLUDED.emb""",
                (kind, path, ts, txt, list(map(float, v))),
            )
        conn.commit()
    return len(items)


def cosine(a, b):
    na = np.linalg.norm(a) + 1e-9
    nb = np.linalg.norm(b) + 1e-9
    return float(np.dot(a, b) / (na * nb))


def compute(conn, goal_text, embf):
    with conn.cursor() as cur:
        cur.execute("SELECT id,kind,path,ts,txt,emb FROM items")
        rows = cur.fetchall()
    if not rows:
        return {"stat": {"delta": None}, "ranking": []}
    texts = [r[4] for r in rows]
    V = embf(texts)
    C = np.mean(V, axis=0)
    C /= np.linalg.norm(C) + 1e-9
    G = embf([goal_text])
    G = G[0]
    G /= np.linalg.norm(G) + 1e-9
    sims_G = V @ G
    sims_C = V @ C
    contrib = sims_G - sims_C
    order = np.argsort(contrib)
    top_neg = order[:3]
    top_pos = order[-3:]
    ranking = []
    for idx in list(top_pos[::-1]) + list(top_neg):
        i = int(idx)
        r = rows[i]
        ranking.append(
            {
                "kind": r[1],
                "path": r[2],
                "delta_sim": round(float(contrib[i]), 4),
                "simG": round(float(sims_G[i]), 4),
                "simC": round(float(sims_C[i]), 4),
                "preview": (r[4] or "")[:140].replace("\n", " "),
            }
        )
    d_vec = G - C
    stat = {"delta": round(float(np.linalg.norm(d_vec)), 4)}
    return {"stat": stat, "ranking": ranking}


def main():
    embf, name = try_sbert()
    if embf is None:
        embf, name = emb_hash
    items, goal = load_corpus()
    conn = psycopg.connect(
        "host=127.0.0.1 port=5432 dbname=egspace user=egspace password=egspace-pass"
    )
    n = upsert(conn, items, embf)
    out = compute(conn, goal, embf)
    result = {"embeddings": name, "count": n, "goal": goal, **out}
    # evidence を直接出力（パスは環境変数）
    evid_path = os.environ.get("EVID_PATH")
    if evid_path:
        with open(evid_path, "w", encoding="utf-8") as f:
            f.write(
                f"# P3-6b EG-Space indexing v1 ({time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())})\n\n"
            )
            f.write(f"- embeddings  : {name}\n")
            f.write(f"- items upsert: {n}\n")
            f.write(f"- goal(text)  : {goal[:200]}\n\n")
            f.write("## C/G/δ\n```json\n")
            f.write(json.dumps(result["stat"], ensure_ascii=False, indent=2))
            f.write(
                "\n```\n\n## 寄与トップ（近づけた→上位3 / 遠ざけた→上位3）\n```json\n"
            )
            f.write(json.dumps(result["ranking"], ensure_ascii=False, indent=2))
            f.write("\n```\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
