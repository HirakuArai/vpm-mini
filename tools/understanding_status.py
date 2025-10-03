#!/usr/bin/env python3
import re
import json
import yaml
import subprocess
from pathlib import Path


def gh_json(args):
    try:
        out = subprocess.check_output(args, text=True)
        out_str = out.strip()
        if not out_str:
            return None
        if out_str.startswith("{") or out_str.startswith("["):
            return json.loads(out_str)
        return None
    except Exception:
        return None


def latest_understanding_ci():
    run = gh_json(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            "understanding-ci",
            "--limit",
            "1",
            "--json",
            "databaseId,conclusion,url",
        ]
    )
    if not run or not isinstance(run, list) or not run:
        return {"conclusion": "absent", "url": None}
    r = run[0]
    return {"conclusion": r.get("conclusion") or "absent", "url": r.get("url")}


def diag_missing(pr_number: int | None):
    if not pr_number:
        return []
    js = gh_json(["gh", "issue", "comments", str(pr_number), "--json", "body"])
    if not js:
        return []
    bodies = [x.get("body", "") for x in js if isinstance(x, dict)]
    for body in reversed(bodies):
        if "### Diag: required vs reported" in body:
            m = re.search(r"\*\*missing\*\*:\s*(.*)", body)
            if not m:
                return []
            txt = m.group(1).strip()
            if not txt or txt in ("[]", "(none)", "-"):
                return []
            items = [t.strip() for t in re.split(r"[,\\n]+", txt) if t.strip()]
            return items
    return []


def goals_state():
    p = Path("STATE/current_state.md")
    if not p.exists():
        return ""
    try:
        s = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    m = re.search(r"^short_goal:\s*(.+)$", s, re.M)
    return (m.group(1).strip().strip("\"'")) if m else ""


def goals_understanding():
    p = Path("config/understanding.yaml")
    if not p.exists():
        return ""
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    return data.get("goals", {}).get("short", "")


def latest_evidence():
    ev = sorted(Path("reports").glob("evidence_*"), reverse=True)
    return ev[0].as_posix() if ev else "(none)"


def build_status(pr_number: int | None):
    uc = latest_understanding_ci()
    snapshot = "success" if (uc.get("conclusion") == "success") else "absent"
    missing = diag_missing(pr_number)
    state_goal = goals_state()
    understanding_goal = goals_understanding()
    goals_equal = bool(
        state_goal and understanding_goal and state_goal == understanding_goal
    )
    ok = (snapshot == "success") and (missing == []) and goals_equal
    return {
        "ok": ok,
        "snapshot": snapshot,
        "understanding_ci_url": uc.get("url"),
        "diag_missing": missing,
        "goals_equal": goals_equal,
        "goal_state": state_goal,
        "goal_understanding": understanding_goal,
        "evidence": latest_evidence(),
    }


def as_markdown(status: dict):
    header = (
        "🧭 Understanding — OK"
        if status["ok"]
        else "🧭 Understanding — NEEDS ATTENTION"
    )
    missing = "0" if status["diag_missing"] == [] else ", ".join(status["diag_missing"])
    goals = "yes" if status["goals_equal"] else "no"
    # Evidence を可能であれば GitHub の blob URL に変換
    ev = status["evidence"]
    ev_link = ev
    if ev != "(none)":
        try:
            import subprocess

            remote = subprocess.check_output(
                ["git", "remote", "get-url", "origin"], text=True
            ).strip()
            match = re.search(r"github.com[:/](.*?)(?:\\.git)?$", remote)
            if match:
                repo = match.group(1)
                branch = subprocess.check_output(
                    [
                        "gh",
                        "repo",
                        "view",
                        "--json",
                        "defaultBranchRef",
                        "-q",
                        ".defaultBranchRef.name",
                    ],
                    text=True,
                ).strip()
                ev_link = f"https://github.com/{repo}/blob/{branch}/{ev}"
        except Exception:
            pass

    lines = [
        header,
        f"- Snapshot: {status['snapshot']}",
        f"- Diag missing: {missing}",
        f"- Goals synced: {goals}",
        f"- Evidence: {ev_link}",
    ]
    if status.get("understanding_ci_url"):
        lines.append(f"- understanding-ci: {status['understanding_ci_url']}")
    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, default=0)
    parser.add_argument("--format", choices=["json", "md", "summary"], default="md")
    args = parser.parse_args()

    status = build_status(args.pr if args.pr > 0 else None)

    if args.format == "json":
        print(json.dumps(status, ensure_ascii=False))
    elif args.format == "summary":
        diag = "none" if status["diag_missing"] == [] else "present"
        goals = "yes" if status["goals_equal"] else "no"
        print(
            f"SUMMARY: snapshot={status['snapshot']}; diag_missing={diag}; goals_equal={goals}"
        )
    else:
        print(as_markdown(status))


if __name__ == "__main__":
    main()
