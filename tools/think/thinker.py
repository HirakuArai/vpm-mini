#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal, indent-safe Thinker:
- reads latest reports/ask/ask_*.json (or by --issue)
- writes reports/think/plan_<ts>.md and think_<ts>.json
- creates a feature branch and a draft PR with --body-file (no shell interpolation)
- optional --execute: run allow-listed commands, write reports/think/exec_<ts>.log,
  commit the log and comment the PR with its path
- never commits ask JSON; uses spaces only (no tabs)
"""

from __future__ import annotations
import argparse
import json, os, sys, glob, subprocess, shlex, textwrap
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
ASK_DIR = ROOT / "reports" / "admin"  # fallback if moved
FALLBACK_ASK = ROOT / "reports" / "ask"
THINK_DIR = ROOT / "reports" / "think"

def run(cmd: list[str], check=True, capture=False, cwd: Path|None=None) -> str|int:
    """Run a command; return stdout text if capture=True, else return returncode."""
    if not isinstance(cmd, (list, tuple)):
        raise TypeError("run() expects list/tuple")
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          text=True, capture_output=capture)
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(proc.returncode)
    return proc.stdout if capture else proc.returncode

def shline(line: str, check=True, capture=False, cwd: Path|None=None) -> str|int:
    return run(shlex.split(line), check=check, capture=capture, cwd=cwd)

def latest_ask_path(issue: str|None) -> Path:
    roots = [ROOT / "reports" / "ask"]
    if ASK_DIR.exists():
        roots.insert(0, ASK_DIR)
    candidates: list[Path] = []
    for r in roots:
        candidates += sorted(r.glob("ask_*.json"))
    if not candidates:
        sys.exit("no reports/ask/ask_*.json found")
    if issue:
        # prefer one whose JSON .meta.issue == issue
        for p in reversed(candidates):
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                if str(obj.get("meta", {}).get("issue")) == str(issue):
                    return p
            except Exception:
                pass
    return candidates[-1]

def allowlist_ok(argv: list[str]) -> bool:
    if not argv:
        return False
    cmd = argv[0]
    if cmd == "kubectl":
        # allow only very safe subcommands
        return any(argv[1:2] and argv[1] in {"get","describe","apply","wait"})  # minimal
    if cmd == "curl":
        return True
    if cmd in {"echo"}:
        return True
    return False

def exec_plan(commands: list[list[str]], dry_run: bool, pr_number: str, ts: str) -> Path:
    THINK_DIR.mkdir(parents=True, exist_ok=True)
    log_path = THINK_DIR / f"exec_{ts}.log"
    with log_path.open("w", encoding="utf-8") as fw:
        for c in commands:
            if not isinstance(c, (list, tuple)):
                # also accept a single string and split it
                if isinstance(c, str):
                    c = shlex.split(c)
                else:
                    continue
            line = " ".join(shlex.quote(x) for x in c)
            fw.write(f"$ {line}\n")
            if not allowlist_ok(list(c)):
                fw.write(f"  [skip] not in allowlist\n\n")
                continue
            if dry_run:
                fw.write("  [dry-run]\n\n")
                continue
            proc = subprocess.run(c, text=True, capture_output=True)
            if proc.stdout:
                fw.write(proc.stdout)
            if proc.stderr:
                fw.write(proc.stderr)
            fw.write("\n")
    # commit the log & comment on PR
    shline(f"git add {shlex.quote(str(log_path.relative_to(ROOT)))}")
    shline(f'git commit -m "think: exec log {ts}"', check=True)
    shline("git push", check=True)
    # comment with PR number; gh prints nothing on success
    shline(f"gh pr comment {pr_number} --body "
           f"{shlex.quote('Exec log: ' + str(log_path.relative_path_to(ROOT) if hasattr(log_path,'relative_path_to') else str(log_path.relative_to(ROOT))))}",
           check=False)
    return log_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", help="numeric issue id to prefer from reports/ask")
    ap.add_argument("--dry-run", action="store_true", help="do not execute external commands")
    ap.add_argument("--execute", action="store_true", default=False)
    args = ap.parse_args()

    # discover ask JSON
    ask_path = latest_ask_path(args.issue)
    obj = json.loads(ask_path.read_json()) if hasattr(Path, "read_json") else json.loads(ask_path.read_text())
    understanding = str(obj.get("understanding", "") or "")
    plan = obj.get("plan") or {}
    raw_cmds = plan.get("commands") or []
    # normalize commands to list[list[str]]
    norm_cmds: list[list[str]] = []
    for x in raw_cmds:
        if isinstance(x, str):
            norm_cmds.append(shlex.split(x))
        elif isinstance(x, (list, tuple)):
            norm_cmds.append([str(y) for y in x])
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    THINK_DIR.mkdir(parents=True, exist_ok=True)
    plan_md = THINK_DIR / f"plan_{ts}.md"
    think_json = THINK_DIR / f"think_{ts}.json"
    body_md = THINK_DIR / f"body_{ts}.md"

    # write artefacts
    plan_md.write_text(
        f"# metrics-echo plan {ts}\n\n"
        f"source_ask: `{ask_path.relative_to(ROOT)}`\n\n"
        f"## understanding\n{understanding}\n\n"
        f"## plan.commands\n" +
        "".join(f"- `{ ' '.join(shlex.quote(t) for t in cmd)}`\n" for cmd in norm_cmds),
        encoding="utf-8"
    )
    think_json.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_ask": str(ask_path.relative_to(ROOT)),
        "issue": args.issue,
        "dry_run": bool(args.dry_run),
        "plan": {"commands": [" ".join(c) for c in norm_cmds]},
        "understanding": understanding
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    body_md.write_text(
        "Draft plan generated by Thinker.\n\n"
        f"- source_ask: `{ask_path.relative_to(ROOT)}`\n"
        f"- dry_run: {args.dry_run}\n",
        encoding="utf-8"
    )

    # git/PR
    shline("git fetch origin --quiet", check=False)
    shline("git switch -q main", check=False)
    shline("git pull --ff-only --quiet", check=False)
    branch = f"think/plan-{ts}"
    shline(f"git switch -c {branch}", check=True)
    # never commit ask JSON
    shline(f"git add {shlex.quote(str(plan_md.relative_to(ROOT)))}")
    shline(f"git add {shlex.quote(str(think_json.relative_to(ROOT)))}", check=False)  # do not fail if ignored
    shline(f'git commit -m "think: plan {ts} (draft via thinker)"', check=True)
    shline("git push -u origin HEAD", check=True)
    url = run([
        "gh","pr","create",
        "-t", f"think: plan {ts}",
        "--draft",
        "--body-file", str(body_md),
        "-H", branch,
        "-B", "main"
    ], capture=True).strip()
pr_number = (out.rsplit("/", 1)[-1].lstrip("#") if out else "")
if not pr_number:
    # 最後の手段: ヘッドブランチからPR番号を引く
    pr_number = run([
        "gh","pr","list","--head", branch,"--json","number","-q",".[0].number"
    ], capture=True,).strip()

    # optional execution
    if args.execute:
        exec_plan(norm_cmds, args.dry_run, pr_number, ts)

if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        raise
    except Exception as e:
        sys.stderr.write(f"[thinker] error: {e}\n")
        sys.exit(1)
