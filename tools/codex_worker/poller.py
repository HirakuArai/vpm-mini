#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

import requests

REPO = os.environ.get("REPO", "HirakuArai/vpm-mini")
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
SEEN = set()  # de-dup within process
CACHE = pathlib.Path.home() / ".cache" / "codex_worker"
CACHE.mkdir(parents=True, exist_ok=True)
SEEN_FILE = CACHE / "requests_seen.txt"
SEEN_FILE.touch(exist_ok=True)


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def seen_add(x):
    with open(SEEN_FILE, "a+") as f:
        f.write(x + "\n")


def seen_has(x):
    with open(SEEN_FILE) as f:
        return any(line.strip() == x for line in f)


def gh(path, method="GET", **kw):
    r = requests.request(method, f"https://api.github.com{path}", headers=HEADERS, **kw)
    if r.status_code >= 300:
        raise RuntimeError(f"GH {method} {path} -> {r.status_code} {r.text[:200]}")
    if r.text.strip() == "":
        return {}
    return r.json()


def comment(issue_num, body):
    gh(f"/repos/{REPO}/issues/{issue_num}/comments", method="POST", json={"body": body})


def get_open_issues_with(label):
    return gh(f"/repos/{REPO}/issues?state=open&labels={label}")


def ensure_git_user(repo_dir):
    subprocess.run(
        ["git", "config", "user.name", "codex-worker"], cwd=repo_dir, check=False
    )
    subprocess.run(
        ["git", "config", "user.email", "codex-worker@example.invalid"],
        cwd=repo_dir,
        check=False,
    )


def git_checkout_safe(repo_dir, work_branch):
    subprocess.run(["git", "fetch", "origin", "--prune"], cwd=repo_dir, check=True)
    r = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", work_branch],
        cwd=repo_dir,
    )
    if r.returncode == 0:
        subprocess.run(
            ["git", "checkout", "-B", work_branch, f"origin/{work_branch}"],
            cwd=repo_dir,
            check=True,
        )
    else:
        subprocess.run(["git", "checkout", "-b", work_branch], cwd=repo_dir, check=True)


def run_once(issue):
    num = issue["number"]
    labels = [label["name"] for label in issue.get("labels", [])]
    if "Approve" not in labels:
        return  # approval gate
    body = issue.get("body", "")
    m = re.search(r"(?is)```json\s*(\{[\s\S]*?\})\s*```", body) or re.search(
        r"(?is)/codex\s+run\s*(\{[\s\S]*\})", body
    )
    if not m:
        return
    contract = json.loads(m.group(1))
    # de-dup id
    request_id = sha(f"{REPO}#{num}#{body.strip()}")
    if request_id in SEEN or seen_has(request_id):
        return
    SEEN.add(request_id)
    seen_add(request_id)

    work_branch = contract.get("work_branch", "feat/codex-run")
    tasks = contract.get("tasks", [])
    acceptance = contract.get("acceptance", [])
    repo_dir = tempfile.mkdtemp(prefix="vpm-")
    subprocess.run(
        ["git", "clone", f"https://github.com/{REPO}.git", repo_dir], check=True
    )
    ensure_git_user(repo_dir)
    git_checkout_safe(repo_dir, work_branch)

    try:
        # execute tasks (very minimal; commands run in bash -lc)
        for t in tasks:
            for cmd in t.get("commands", []):
                subprocess.run(["bash", "-lc", cmd], cwd=repo_dir, check=True)
        # acceptance
        ok = True
        for a in acceptance:
            r = subprocess.run(["bash", "-lc", a], cwd=repo_dir)
            if r.returncode != 0:
                ok = False
                break
        if not ok:
            comment(num, ":warning: Acceptance failed. No PR created.")
            return
        # stage artifacts if any path exists
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "codex: run-contract apply"],
            cwd=repo_dir,
            check=True,
        )
        subprocess.run(["git", "push", "origin", work_branch], cwd=repo_dir, check=True)
        pr = gh(
            f"/repos/{REPO}/pulls",
            method="POST",
            json={
                "head": work_branch,
                "base": "main",
                "title": "codex: run-contract",
                "body": "Automated by devbox Codex. Includes artifacts in reports/ if any.",
            },
        )
        comment(num, f":rocket: Started. PR #{pr['number']} opened.")
    except Exception as e:
        comment(num, f":x: Execution error: `{str(e)[:180]}`. No PR created.")
        return


def main():
    while True:
        try:
            # only issues explicitly queued for codex AND open
            items = get_open_issues_with("codex:queued")
            for it in items:
                run_once(it)
        except Exception as e:
            sys.stderr.write(f"[loop-error] {e}\n")
        time.sleep(20)


if __name__ == "__main__":
    main()
