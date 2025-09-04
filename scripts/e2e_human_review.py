import json
import difflib
import pathlib

seed_raw = pathlib.Path("tests/e2e/semantic_seed.jsonl")
seed_enr = pathlib.Path("reports/_semantic_seed_enriched.jsonl")
out = pathlib.Path("reports/e2e_human_review.md")


def load_items():
    path = seed_enr if seed_enr.exists() else seed_raw
    items = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        items.append(json.loads(line))
    return items


def sim_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


items = []
for o in load_items():
    raw = o["raw"].strip()
    exp = o["digest_expected"].strip()
    sim = sim_ratio(raw, exp)
    o["_sim"] = sim
    items.append(o)

items.sort(key=lambda x: x["_sim"])  # worst first
N = min(5, len(items))
with out.open("w", encoding="utf-8") as f:
    f.write("# E2E Human Review v2 (worst {} of {})\n\n".format(N, len(items)))
    f.write(
        "**含まれる情報**: ソース抜粋 / GitHubリンク / 期待要約 / 差分 / 判定欄\n\n"
    )
    for i in range(N):
        o = items[i]
        sim = o["_sim"]
        f.write(f"## {i+1}. id={o.get('id','?')} (sim≈{sim:.3f})\n\n")
        src = o.get("source")
        if src:
            f.write(f"**Source**: `{src['path']}` L{src['start']}-{src['end']}  ")
            if src.get("link"):
                f.write(f"[🔗open]({src['link']})")
            f.write("\n\n```text\n" + src["snippet"] + "\n```\n\n")
        else:
            f.write("_Source not found (auto search failed)_\n\n")
        f.write("**expected**\n\n> " + o["digest_expected"].strip() + "\n\n")
        f.write("**diff (raw vs expected)**\n\n```diff\n")
        for line in difflib.unified_diff(
            o["raw"].split(), o["digest_expected"].split(), lineterm=""
        ):
            f.write(line + "\n")
        f.write("```\n\n")
        f.write("- [ ] Accept  /  - [ ] Revise\n\n---\n\n")
print(f"[OK] wrote {out}")
