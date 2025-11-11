#!/usr/bin/env python3
# Safe executor for Thinker: allow-listed kubectl/curl/echo only.
import argparse
import os
import shlex
import subprocess
import sys
import time


ALLOWED = {"get", "describe", "wait"}


def kubectl_subcommand(argv):
    """
    左から走査して最初に現れた許可サブコマンドを返す。
    """
    for token in argv[1:]:
        if token in ALLOWED:
            return token
    return None


def ensure_wait_timeout(argv):
    """
    kubectl wait に --request-timeout を強制的に付与する。
    """
    for token in argv[1:]:
        if token.startswith("--request-timeout"):
            return False
        if token == "--request-timeout":
            return False
    argv.append("--request-timeout=30s")
    return True


def run_one(cmd, log, dry):
    parts = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    if not parts:
        log.write("[deny] empty command\n")
        return 0
    prog = parts[0]
    subcmd = None
    if prog == "kubectl":
        subcmd = kubectl_subcommand(parts)
        if subcmd == "wait":
            ensure_wait_timeout(parts)
        ok = subcmd is not None
    elif prog in {"curl", "echo"}:
        ok = True
    else:
        ok = False

    line = " ".join(shlex.quote(x) for x in parts)
    log.write(f"$ {line}\n")

    if not ok:
        log.write("  [skip] not in allowlist\n\n")
        return 0
    if dry:
        log.write("  [dry-run]\n\n")
        return 0

    try:
        p = subprocess.run(parts, text=True, capture_output=True, timeout=40)
    except subprocess.TimeoutExpired as exc:
        log.write(f"  [timeout] command exceeded 40s: {exc}\n\n")
        return 1

    if p.stdout:
        log.write(p.stdout)
    if p.stderr:
        log.write(p.stderr)
    log.write("\n")
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commands", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--log", default=f"reports/think/exec_{int(time.time())}.log")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
    rc = 0
    with open(args.log, "a", encoding="utf-8") as lw:
        for c in args.commands:
            rc |= run_one(c, lw, args.dry_run)
    print(args.log)
    sys.exit(rc)


if __name__ == "__main__":
    main()
