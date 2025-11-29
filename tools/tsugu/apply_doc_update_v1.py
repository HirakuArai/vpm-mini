from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List


def run_cmd(
    cmd: List[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def ensure_clean_git():
    res = run_cmd(["git", "status", "--porcelain"])
    if res.stdout.strip():
        sys.stderr.write("Working tree is not clean. Please run on a clean checkout.\n")
        sys.exit(1)


def download_review(run_id: str, artifact_name: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        run_cmd(["gh", "run", "download", run_id, "-n", artifact_name, "-D", str(dest)])
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(
            f"Failed to download artifact {artifact_name} from run {run_id}: {exc.stderr}\n"
        )
        sys.exit(1)

    candidates = list(dest.rglob("doc_update_review_v1.json"))
    if not candidates:
        sys.stderr.write("doc_update_review_v1.json not found in downloaded artifact\n")
        sys.exit(1)
    if len(candidates) > 1:
        sys.stderr.write(
            "Multiple doc_update_review_v1.json files found; refusing to pick automatically\n"
        )
        sys.exit(1)
    return candidates[0]


def load_review(path: Path) -> Dict:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Failed to load review JSON: {exc}\n")
        sys.exit(1)


def validate_review(review: Dict):
    review_mode = review.get("review_mode") or review.get("decision")
    if review_mode not in ("auto_accept_v1", "auto_accept_all"):
        sys.stderr.write(f"Unsupported review_mode/decision: {review_mode}\n")
        sys.exit(1)

    updates = review.get("updates") or []
    if not updates:
        sys.stderr.write("No updates found in review\n")
        sys.exit(1)

    per_path = {}
    for upd in updates:
        path = upd.get("target", {}).get("path") or upd.get("target_path")
        if not path:
            sys.stderr.write("Update without target path; aborting\n")
            sys.exit(1)
        if not (path.startswith("STATE/") or path.startswith("docs/")):
            sys.stderr.write(
                f"Unsupported target path (only STATE/ and docs/ allowed): {path}\n"
            )
            sys.exit(1)
        if upd.get("risk") != "low":
            sys.stderr.write(f"Update risk is not low for {path}\n")
            sys.exit(1)
        final_content = upd.get("final_content")
        if not isinstance(final_content, str) or not final_content.strip():
            sys.stderr.write(f"final_content missing or invalid for {path}\n")
            sys.exit(1)
        if path in per_path:
            sys.stderr.write(
                f"Multiple final_content entries for the same path (path={path})\n"
            )
            sys.exit(1)
        per_path[path] = final_content
    return per_path


def write_updates(updates: Dict[str, str]):
    for rel_path, content in updates.items():
        path = Path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def create_branch_commit_pr(branch: str, run_id: str, files: List[str]):
    run_cmd(["git", "checkout", "-b", branch])
    run_cmd(["git", "add"] + files)
    run_cmd(
        ["git", "commit", "-m", f"docs(state): apply doc_update_review_v1 run {run_id}"]
    )

    body_lines = [
        f"Applied doc_update_review_v1 from Actions run `{run_id}`.",
        "",
        "Updated files:",
    ] + [f"- {p}" for p in files]

    run_cmd(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"Docs: apply doc_update_review_v1 (run {run_id}) to STATE/docs",
            "--body",
            "\n".join(body_lines),
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Apply doc_update_review_v1.json (Tsugu v1)."
    )
    parser.add_argument(
        "--project-id", required=True, help="Project ID (vpm-mini for v1)."
    )
    parser.add_argument(
        "--review-run-id",
        required=True,
        help="GitHub Actions run id producing doc_update_review_v1.",
    )
    parser.add_argument(
        "--review-artifact-name",
        default="doc_update_review_v1",
        help="Artifact name containing doc_update_review_v1.json (default: doc_update_review_v1).",
    )
    args = parser.parse_args()

    if args.project_id != "vpm-mini":
        sys.stderr.write(f"Unsupported project_id for v1: {args.project_id}\n")
        sys.exit(1)

    ensure_clean_git()

    with tempfile.TemporaryDirectory() as tmpdir:
        review_path = download_review(
            args.review_run_id, args.review_artifact_name, Path(tmpdir)
        )
        review = load_review(review_path)
        updates = validate_review(review)
        write_updates(updates)

    files = list(updates.keys())
    if not files:
        sys.stderr.write("No files to apply\n")
        sys.exit(1)

    branch_name = f"feature/doc-update-apply-{args.review_run_id}"
    create_branch_commit_pr(branch_name, args.review_run_id, files)


if __name__ == "__main__":
    main()
