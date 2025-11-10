#!/usr/bin/env python3
import argparse, subprocess, shlex, sys, time, os
ALLOW = {
  "kubectl": {"args_prefix": ["apply","wait","get","delete","rollout","config","-f","--for=condition=Ready","kservice/"]},
  "curl":    {"args_prefix": ["-fsS","-H","http://","https://"]},
}
def run(cmd, logf, dry):
    parts = shlex.split(cmd)
    if not parts: return 0
    prog = parts[0]
    if prog not in ALLOW:
        logf.write(f"[deny] {cmd}\n"); return 0
    # ざっくり前方一致で危険コマンドを弾く（簡易）
    joined = " ".join(parts[1:])
    ok = any(p in joined for p in ALLOW[prog]["args_prefix"])
    if not ok:
        logf.write(f"[deny] {cmd}\n"); return 0
    if dry:
        logf.write(f"[dry]  {cmd}\n"); return 0
    logf.write(f"[exec] {cmd}\n")
    p = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logf.write(p.stdout or "")
    return p.returncode
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commands", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--log", default=f"reports/think/exec_{int(time.time())}.log")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    rc = 0
    with open(args.log, "a") as lf:
        for c in args.commands:
            rc |= run(c, lf, args.dry_run)
    print(args.log)
    sys.exit(rc)
if __name__ == "__main__":
    main()
