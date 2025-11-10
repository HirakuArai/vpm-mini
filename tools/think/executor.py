#!/usr/bin/env python3
# Safe executor for Thinker: allow-listed kubectl/curl/echo only.
import argparse, shlex, subprocess, sys, time, os

def allow_kubectl(argv):
    """
    flags(-n/--namespace 等)とその値を飛ばして最初のサブコマンドを拾う。
    読み取り系(get/describe)は常にOK。apply/waitは後で本番化。
    """
    i = 1
    needs_val = {
        "-n","--namespace","-f","--filename","-o","--output",
        "-l","--selector","--context","--kubeconfig"
    }
    while i < len(argv):
        a = argv[i]
        if not a.startswith("-"):
            sub = a
            return sub in {"get","describe","apply","wait"}
        if a in needs_val and i + 1 < len(argv):
            i += 2
            continue
        i += 1
    return False

def run_one(cmd, log, dry):
    parts = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    if not parts:
        log.write("[deny] empty command\n")
        return 0
    prog = parts[0]
    line = " ".join(shlex.quote(x) for x in parts)
    log.write(f"$ {line}\n")

    ok = False
    if prog == "kubectl":
        ok = allow_kubectl(parts)
    elif prog in {"curl", "echo"}:
        ok = True

    if not ok:
        log.write("  [skip] not in allowlist\n\n")
        return 0
    if dry:
        log.write("  [dry-run]\n\n")
        return 0

    p = subprocess.run(parts, text=True, capture_output=True)
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
