#!/usr/bin/env python3
import argparse, json, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commands", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true", default=True)
    args = ap.parse_args()

    if not args.commands:
        print("[executor] no commands to run; exiting 0", file=sys.stderr)
        return 0

    for i, cmd in enumerate(args.commands, 1):
        if args.dry_run:
            print(f"[dry-run] ({i}) {cmd}")
        else:
            print(f"[exec] ({i}) {cmd}")
            # 安全プリミティブに置換予定。現状はシェル禁止。
            # subprocess.run(cmd, check=True, shell=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())
