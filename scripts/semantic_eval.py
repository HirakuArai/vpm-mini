import json
import sys
import time
import difflib
import pathlib

inp = pathlib.Path("tests/e2e/semantic_seed.jsonl")
out = pathlib.Path("reports/quality.json")
if not inp.exists():
    print("no samples found", file=sys.stderr)
    sys.exit(1)
N = 0
total = 0.0
too_long = 0
items = []
for line in inp.read_text().splitlines():
    if not line.strip():
        continue
    o = json.loads(line)
    raw = o["raw"].strip()
    exp = o["digest_expected"].strip()
    sim = difflib.SequenceMatcher(
        None, raw, exp
    ).ratio()  # proxy; later replace with ROUGE/emb
    total += sim
    N += 1
    if len(exp) > 400:
        too_long += 1
    items.append({"id": o["id"], "len": len(exp), "sim_proxy": round(sim, 4)})
result = {
    "ts": int(time.time()),
    "samples": N,
    "avg_sim_proxy": round(total / max(N, 1), 4),
    "len_le400_ok": (too_long == 0),
    "items": items,
}
out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(f"[OK] wrote {out}")
print(json.dumps(result, ensure_ascii=False, indent=2))
