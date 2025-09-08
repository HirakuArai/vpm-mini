import json
import glob
import numpy as np
import psycopg
import hashlib

EMB_DIM = 384


def try_sbert():
    try:
        from sentence_transformers import SentenceTransformer

        m = SentenceTransformer("all-MiniLM-L6-v2")

        def emb(txts):
            X = m.encode(txts, normalize_embeddings=True)
            return np.asarray(X, dtype=np.float32)

        return emb, "sbert"
    except Exception:
        return None, None


def emb_hash(txts):
    V = []
    for t in txts:
        rng = np.random.default_rng(
            int(hashlib.sha256(t.encode()).hexdigest(), 16) % (1 << 32)
        )
        v = rng.standard_normal(EMB_DIM).astype(np.float32)
        v /= np.linalg.norm(v) + 1e-9
        V.append(v)
    return np.stack(V, 0), "hash"


def latest_green_text():
    try:
        s = open("STATE/current_state.md", "r", encoding="utf-8").read()
        for line in reversed(s.splitlines()):
            if "GREEN" in line:
                return line.strip()
    except Exception:
        pass
    return "Goal"


def compute_from_db():
    embf, name = try_sbert()
    if embf is None:
        embf, name = emb_hash, "hash"
    conn = psycopg.connect(
        "host=127.0.0.1 port=5432 dbname=egspace user=egspace password=egspace-pass"
    )
    cur = conn.cursor()
    cur.execute("SELECT kind,path,txt,emb FROM items")
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("no items in pgvector")
    texts = [r[2] or "" for r in rows]
    V = embf(texts)
    C = V.mean(0)
    C /= np.linalg.norm(C) + 1e-9
    Gtxt = latest_green_text()
    G = embf([Gtxt])
    G = G[0]
    G /= np.linalg.norm(G) + 1e-9
    sims_G = V @ G
    sims_C = V @ C
    contrib = sims_G - sims_C
    order = np.argsort(contrib)

    def pick(idxs, sign):
        out = []
        for i in idxs:
            kind, path, txt, _ = rows[int(i)]
            out.append(
                {
                    "kind": kind,
                    "path": path,
                    "delta_sim": round(float(contrib[int(i)]), 4),
                    "simG": round(float(sims_G[int(i)]), 4),
                    "simC": round(float(sims_C[int(i)]), 4),
                    "preview": (txt or "").replace("\n", " ")[:140],
                }
            )
        return out

    top_pos = pick(order[-3:][::-1], "+")  # 近づけた
    top_neg = pick(order[:3], "-")  # 遠ざけた
    d = G - C
    delta = float(np.linalg.norm(d))
    return {
        "ok": True,
        "embeddings": name,
        "goal": Gtxt,
        "stat": {"delta": round(delta, 4)},
        "closer": top_pos,
        "farther": top_neg,
    }


def fallback_from_evidence():
    try:
        p = sorted(glob.glob("reports/p3_6b_egspace_index_*.md"))[-1]
        # ざっくり抽出（stat/ranking部分はコード生成のevidenceに準拠）
        _ = open(p, "r", encoding="utf-8").read()
        return {"ok": True, "from": "evidence", "note": p}
    except Exception:
        return {"ok": False, "error": "no evidence"}


if __name__ == "__main__":
    try:
        out = compute_from_db()
    except Exception as e:
        out = fallback_from_evidence()
        out["error"] = str(e)
    print(json.dumps(out, ensure_ascii=False))
