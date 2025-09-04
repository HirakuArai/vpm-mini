import os
import re
import json
import pathlib
import subprocess

ROOT = pathlib.Path(".").resolve()
SEED = ROOT / "tests/e2e/semantic_seed.jsonl"
ENR = ROOT / "reports/_semantic_seed_enriched.jsonl"

STOP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
    ".idea",
    ".vscode",
    ".mypy_cache",
}
TEXT_EXT = {
    ".md",
    ".txt",
    ".py",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".mdx",
    ".ini",
    ".cfg",
    ".toml",
    ".sql",
    ".go",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
}
EXTRA_KEYS = {
    "knative",
    "kservice",
    "hello",
    "ko.local",
    "kourier",
    "serving",
    "configmap",
    "secret",
    "x-dur-ms",
    "p50",
    "p95",
    "avg",
    "gatekeeper",
    "spiffe",
    "do d",
    "auto-merge",
    "--dry-run=client",
    ":latest",
}


def iter_files(root: pathlib.Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # prunes
        dirnames[:] = [
            d for d in dirnames if d not in STOP_DIRS and not d.startswith(".git")
        ]
        for fn in filenames:
            p = pathlib.Path(dirpath) / fn
            suf = p.suffix.lower()
            if suf in TEXT_EXT or suf == "" and p.stat().st_size < 2_000_000:
                yield p


def keywords(text: str):
    # pick tokens that look like terms/symbols
    toks = re.findall(r"[A-Za-z][A-Za-z0-9_.:-]{2,}|:[a-z]+|--[a-z-]+", text)
    lows = {t.lower() for t in toks}
    lows |= EXTRA_KEYS
    return lows


def best_anchor(kws, path):
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        return None
    best = (-1, None, None)  # (score, line_idx, matched_words)
    for i, ln in enumerate(lines):
        ln_l = ln.lower()
        hit = [w for w in kws if w in ln_l]
        score = len(hit)
        if score > best[0]:
            best = (score, i, hit)
    if best[0] <= 0:
        return None
    i = best[1]
    s = max(0, i - 2)
    e = min(len(lines), i + 3)
    return {
        "path": str(path.relative_to(ROOT)),
        "line": i + 1,
        "start": s + 1,
        "end": e,
        "hits": best[2],
        "snippet": "\n".join(lines[s:e]),
    }


def git_remote_https():
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        if url.startswith("git@"):
            # git@github.com:Owner/Repo.git -> https://github.com/Owner/Repo
            owner_repo = url.split(":", 1)[1].removesuffix(".git")
            return f"https://github.com/{owner_repo}"
        if url.startswith("https://"):
            return url.removesuffix(".git")
    except Exception:
        pass
    return ""


def git_branch():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
    except Exception:
        return "main"


def main():
    base = git_remote_https()
    br = git_branch()
    out = []
    if not SEED.exists():
        raise SystemExit("seed not found")
    for ln in SEED.read_text().splitlines():
        if not ln.strip():
            continue
        obj = json.loads(ln)
        raw = obj.get("raw", "")
        exp = obj.get("digest_expected", "")
        kws = keywords(raw + " " + exp)
        best = None
        # scan files and choose best score
        for p in iter_files(ROOT):
            a = best_anchor(kws, p)
            if a and (best is None or len(a["hits"]) > len(best["hits"])):
                best = a
        if best:
            link = (
                f"{base}/blob/{br}/{best['path']}#L{best['start']}-L{best['end']}"
                if base
                else ""
            )
            obj["source"] = {
                "path": best["path"],
                "start": best["start"],
                "end": best["end"],
                "link": link,
                "hits": best["hits"],
                "snippet": best["snippet"],
            }
        out.append(obj)
    ENR.parent.mkdir(parents=True, exist_ok=True)
    with ENR.open("w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"[OK] wrote {ENR} ({len(out)} items)")


if __name__ == "__main__":
    main()
