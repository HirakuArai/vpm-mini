#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def run_cmd(cmd: List[str], cwd: Path) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run hakone-e2 update cycle v1.1 (bundle→snapshot→seed plan→suggested plan). Does NOT apply."
    )
    ap.add_argument(
        "--bundle", required=True, help="Path to info_source_bundle_v1 (yaml/json)"
    )
    ap.add_argument("--project-id", default="hakone-e2")
    ap.add_argument("--model", default="gpt-4.1")
    ap.add_argument(
        "--run-dir",
        help="Output dir for artifacts (default: reports/hakone-e2/runs/<timestamp>/)",
    )
    ap.add_argument(
        "--canonical-nodes",
        default="data/hakone-e2/info_nodes_v1.json",
        help="Path to canonical nodes JSON",
    )
    ap.add_argument(
        "--canonical-relations",
        default="data/hakone-e2/info_relations_v1.json",
        help="Path to canonical relations JSON",
    )
    args = ap.parse_args()

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = (
        Path(args.run_dir)
        if args.run_dir
        else Path(f"reports/{args.project_id}/runs/{run_id}")
    )
    ensure_dir(run_dir)

    repo_root = Path(".").resolve()
    bundle_path = Path(args.bundle).resolve()
    snapshot_path = run_dir / "snapshot_raw.json"
    seed_path = run_dir / "seed_plan_v0_1.json"
    suggestion_path = run_dir / "suggestion_plan_v1_1.json"

    # 1) bundle -> snapshot
    run_cmd(
        [
            sys.executable,
            str(repo_root / "tools/info_network/generate_from_bundle_v1.py"),
            "--bundle",
            str(bundle_path),
            "--schema-doc",
            "docs/pm/info_network_v1_schema.md",
            "--model",
            args.model,
            "--output",
            str(snapshot_path),
        ],
        cwd=repo_root,
    )

    # 2) seed plan (v0.1 no-op)
    run_cmd(
        [
            sys.executable,
            str(repo_root / "tools/info_network/generate_update_plan_v0.py"),
            "--canonical-nodes",
            args.canonical_nodes,
            "--canonical-relations",
            args.canonical_relations,
            "--snapshot",
            str(snapshot_path),
            "--output",
            str(seed_path),
        ],
        cwd=repo_root,
    )

    # 3) v1.1 suggestion
    run_cmd(
        [
            sys.executable,
            str(repo_root / "tools/info_network/suggest_update_plan_v1_1.py"),
            "--canonical-nodes",
            args.canonical_nodes,
            "--canonical-relations",
            args.canonical_relations,
            "--snapshot",
            str(snapshot_path),
            "--model",
            args.model,
            "--output",
            str(suggestion_path),
        ],
        cwd=repo_root,
    )

    # 4) Inspect questions to decide next action
    suggestion = json.loads(suggestion_path.read_text(encoding="utf-8"))
    questions = suggestion.get("questions", []) or []
    add_ct = len(suggestion.get("add", []))
    update_ct = len(suggestion.get("update", []))
    supersedes_ct = len(suggestion.get("supersedes", []))
    obsolete_ct = len(suggestion.get("obsolete", []))

    print("\n=== run summary ===")
    print(f"run_dir: {run_dir}")
    print(f"snapshot: {snapshot_path.name}")
    print(f"seed plan: {seed_path.name}")
    print(f"suggestion: {suggestion_path.name}")
    print(
        f"add={add_ct}, update={update_ct}, supersedes={supersedes_ct}, obsolete={obsolete_ct}"
    )
    print(f"questions={len(questions)}")

    if questions:
        print(
            "\n[halt] questions detected. Owner confirmation required. "
            "Do NOT auto-apply. Create an approved plan after resolving questions."
        )
    else:
        approved_path = run_dir / "approved_plan.json"
        print(
            "\n[ok] no questions; you may approve and apply manually. "
            "Example to create approved plan and apply:\n"
        )
        print(
            f"python - <<'EOF'\n"
            f"import json, pathlib\n"
            f"src = pathlib.Path('{suggestion_path}')\n"
            f"d = json.loads(src.read_text(encoding='utf-8'))\n"
            f"d['questions'] = []\n"
            f"d['notes'] = (d.get('notes','') + \"\\n\\n[approved] Owner approved; questions cleared.\").strip()\n"
            f"out = pathlib.Path('{approved_path}')\n"
            f"out.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\\n', encoding='utf-8')\n"
            f"print('wrote', out)\n"
            f"EOF\n"
        )
        print(
            f"python tools/info_network/apply_info_update_plan_v1.py "
            f"--plan {approved_path} --nodes {args.canonical_nodes} --relations {args.canonical_relations}"
        )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:  # noqa: BLE001
        print(f"ERROR: command failed with code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
