#!/usr/bin/env python3
# Safe executor for Thinker: run only allow-listed kubectl/curl/echo commands.
import argparse, shlex, subprocess, sys, time, os

def allow_kubectl(argv):
    # skip flags to find first subcommand token
    sub = ""
    for a in argv[1:]:
        if not a.startswith("-"):
            sub = a
            break
    return sub in {"get", "describe", "apply", "wait"}  # apply/waitはdry-run時のみ実行扱い

def run_one(cmd, log, dry):
    parts = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    if not parts:
        log.write("[deny] empty command\n"); return 0
    prog = parts[0]
    line = " ".join(shlex.quote(x) for x in parts)
    log.write(f"$ {line}\n")

    # allowlist
    ok = False
    if prog == "kubectl":
        ok = allow_kubectl(parts)
    elif prog in {"curl", "echo"}:
        ok = True

    if not ok:
        log.write("  [skip] not in allowlist\n\n"); return 0
    if dry:
        log.write("  [dry-run]\n\n"); return 0

    p = subprocess.run(parts, text=True, capture_output=True)
    if p.stdout: log.write(p.stdout)
    if p.stderr: log.write(p.stderr)
    log.write("\n")
    return p.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commands", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--log", default=f"reports/think/exec_{int(time.time())}.log")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    rc = 0
    with open(args.log, "a", encoding="utf-8") as lw:
        for c in args.commands:
            rc |= run_one(c, lw, args.dry_run)
    print(args.log)
    sys.exit(rc)

if __name__ == "__main__":
    main()
