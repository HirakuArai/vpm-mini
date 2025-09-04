import json
import difflib
import pathlib

seed = pathlib.Path("tests/e2e/semantic_seed.jsonl")
out = pathlib.Path("reports/e2e_human_review.md")
items = []
for line in seed.read_text().splitlines():
    if not line.strip():
        continue
    o = json.loads(line)
    raw = o["raw"].strip()
    exp = o["digest_expected"].strip()
    sim = difflib.SequenceMatcher(None, raw, exp).ratio()
    items.append((1.0 - sim, o["id"], raw, exp, sim))
items.sort(reverse=True)  # worst first
N = min(5, len(items))
with out.open("w", encoding="utf-8") as f:
    f.write("# E2E Human Review (worst {} of {})\n\n".format(N, len(items)))
    for i in range(N):
        _, _id, raw, exp, sim = items[i]
        f.write(f"## {i+1}. id={_id} (sim≈{sim:.3f})\n\n")
        f.write("**raw**\n\n> " + raw + "\n\n")
        f.write("**expected**\n\n> " + exp + "\n\n")
        f.write("**diff (raw vs expected)**\n\n```diff\n")
        for line in difflib.unified_diff(raw.split(), exp.split(), lineterm=""):
            f.write(line + "\n")
        f.write("```\n\n")
print(f"[OK] wrote {out}")
