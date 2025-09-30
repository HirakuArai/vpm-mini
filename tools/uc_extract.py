#!/usr/bin/env python3
"""Generate a lightweight understanding snapshot (JSON + Markdown)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8")

    def grab_scalar(key: str, default: str = "") -> str:
        match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
        if not match:
            return default
        value = match.group(1).strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]
        return value

    def grab_list_block(key: str) -> List[str]:
        block = re.search(rf"^{key}:\s*\n((?:\s+-\s+.+\n)+)", text, re.MULTILINE)
        if block:
            lines = []
            for line in block.group(1).splitlines():
                item = line.strip()[2:].strip()
                if item.startswith(("'", '"')) and item.endswith(("'", '"')):
                    item = item[1:-1]
                lines.append(item)
            return lines
        inline = re.search(rf"^{key}:\s*\[(.*)\]", text, re.MULTILINE)
        if inline:
            inside = inline.group(1).strip()
            if not inside:
                return []
            parts = [part.strip() for part in inside.split(",")]
            cleaned = []
            for part in parts:
                if part.startswith(("'", '"')) and part.endswith(("'", '"')):
                    part = part[1:-1]
                cleaned.append(part)
            return cleaned
        return []

    goals_block = re.search(r"^goals:\s*\n((?:\s{2}.+\n)+)", text, re.MULTILINE)
    goals: Dict[str, str] = {"short": "", "mid": "", "long": ""}
    if goals_block:
        for line in goals_block.group(1).splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith(("'", '"')) and value.endswith(("'", '"')):
                value = value[1:-1]
            goals[key] = value

    config = {
        "project_id": grab_scalar("project_id"),
        "phase": grab_scalar("phase"),
        "state_path": grab_scalar("state_path"),
        "evidence_glob": grab_scalar("evidence_glob"),
        "ruleset_required": grab_list_block("ruleset_required"),
        "branch_required": grab_list_block("branch_required"),
        "goals": goals,
    }
    return config


def repo_slug() -> Tuple[str, str]:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    )
    url = result.stdout.strip()
    if not url:
        raise RuntimeError("remote.origin.url is not configured")
    if url.startswith("git@"):
        slug = url.split(":", 1)[1]
    else:
        slug = url.split("github.com/")[-1]
    if slug.endswith(".git"):
        slug = slug[:-4]
    owner, repo = slug.split("/", 1)
    return owner, repo


def run_gh_api(endpoint: str) -> Tuple[Optional[object], Optional[str]]:
    result = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None, result.stderr.strip() or "gh api failed"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from gh api: {exc}"


def parse_readme_phase(path: Path) -> Optional[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^##\s+Phase\s+([^\n]+)$", text, re.MULTILINE)
    if match:
        return f"Phase {match.group(1).strip()}"
    match = re.search(r"Phase\s+(\d[^\n]*)", text)
    if match:
        return f"Phase {match.group(1).strip()}"
    return None


def parse_state(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8")
    phase_match = re.search(r"^phase:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    phase = phase_match.group(1).strip() if phase_match else None

    lines = text.splitlines()
    highlights: List[str] = []
    capture = False
    for line in lines:
        if line.startswith("- "):
            highlights.append(line[2:].strip())
            capture = True
        elif capture and line.strip() == "":
            break
    pending = [
        line[2:].strip()
        for line in lines
        if "⏳" in line and line.strip().startswith("- ")
    ]

    evidence_links = []
    for line in lines:
        if "reports/" in line:
            match = re.search(r"reports/[\w\-\.]+", line)
            if match:
                evidence_links.append(match.group(0))
    short_goal_match = re.search(r"^short_goal:\s*(.+)$", text, re.MULTILINE)
    short_goal = short_goal_match.group(1).strip() if short_goal_match else None
    return {
        "phase": phase,
        "highlights": highlights,
        "pending": pending,
        "evidence": evidence_links,
        "short_goal": short_goal,
    }


def latest_evidence(glob_pattern: str) -> Optional[str]:
    files = sorted(glob(str(ROOT / glob_pattern)), reverse=True)
    if not files:
        return None
    return str(Path(files[0]).relative_to(ROOT))


def collect_pr_summaries(
    owner: str, repo: str, limit: int = 6
) -> Tuple[List[str], Optional[str]]:
    endpoint = f"repos/{owner}/{repo}/pulls?state=closed&per_page={limit}"
    data, error = run_gh_api(endpoint)
    if error:
        return [], error
    summaries: List[str] = []
    for pr in data:
        if not pr.get("merged_at"):
            continue
        merged_at = pr["merged_at"]
        merged_date = merged_at[:10] if merged_at else ""
        summaries.append(f"PR #{pr['number']}: {pr['title']} (merged {merged_date})")
    return summaries, None


def collect_ruleset_contexts(owner: str, repo: str) -> Tuple[List[str], Optional[str]]:
    listing, error = run_gh_api(f"repos/{owner}/{repo}/rulesets")
    if error:
        return [], error
    contexts: List[str] = []
    for entry in listing:
        if entry.get("target") != "branch":
            continue
        ruleset_id = entry.get("id")
        details, det_error = run_gh_api(f"repos/{owner}/{repo}/rulesets/{ruleset_id}")
        if det_error:
            return [], det_error
        for rule in details.get("rules", []):
            if rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters", {})
            for ctx in params.get("required_status_checks", []):
                context = ctx.get("context") if isinstance(ctx, dict) else ctx
                if context and context not in contexts:
                    contexts.append(context)
    return contexts, None


def collect_branch_contexts(
    owner: str, repo: str, branch: str = "main"
) -> Tuple[List[str], Optional[str]]:
    data, error = run_gh_api(f"repos/{owner}/{repo}/branches/{branch}/protection")
    if error:
        return [], error
    checks = data.get("required_status_checks") if isinstance(data, dict) else None
    if not checks:
        return [], None
    contexts = checks.get("contexts") if isinstance(checks, dict) else None
    if not contexts:
        return [], None
    unique: List[str] = []
    for ctx in contexts:
        if ctx not in unique:
            unique.append(ctx)
    return unique, None


def build_markdown(data: Dict[str, object]) -> str:
    def format_list(items: List[str]) -> str:
        if not items:
            return "- (none)"
        return "\n".join(f"- {item}" for item in items)

    constraints = data.get("constraints", {})
    ruleset = constraints.get("ruleset", {})
    branch = constraints.get("branch", {})

    md_lines = [
        f"# Understanding Snapshot v0 — {data['project']}",
        f"timestamp: {data['timestamp']}",
        f"expected phase: {data['expected'].get('phase', 'unknown')}",
        "",
        "## C",
        format_list(data.get("c", [])),
        "",
        "## G",
    ]
    goals = data.get("g", {})
    md_lines.extend(
        [
            f"- Short: {goals.get('short', '')}",
            f"- Mid: {goals.get('mid', '')}",
            f"- Long: {goals.get('long', '')}",
        ]
    )
    md_lines.extend(
        [
            "",
            "## δ",
            format_list(data.get("delta", [])),
            "",
            "## Constraints",
            f"- Ruleset required: {', '.join(ruleset.get('required', [])) or '(none)'}",
            f"- Ruleset reported: {', '.join(ruleset.get('reported', [])) or '(none)'}",
            f"- Branch required: {', '.join(branch.get('required', [])) or '(none)'}",
            f"- Branch reported: {', '.join(branch.get('reported', [])) or '(none)'}",
            "",
            "## Evidence",
            format_list(data.get("evidence", [])),
            "",
            "## Next (DoD/Reason)",
        ]
    )
    next_entries = data.get("next", [])
    if next_entries:
        for entry in next_entries:
            title = entry.get("title", "")
            dod = entry.get("dod", "")
            reason = entry.get("reason", "")
            md_lines.append(f"- {title} — DoD: {dod} (Reason: {reason})")
    else:
        md_lines.append("- (none)")

    unknowns = data.get("unknowns", {})
    md_lines.extend(["", "## Unknowns"])
    if unknowns:
        for key, value in unknowns.items():
            md_lines.append(f"- {key}: {value}")
    else:
        md_lines.append("- (none)")

    md_lines.extend(["", "## Conflicts / Mismatches"])
    conflicts = data.get("conflicts", [])
    if conflicts:
        md_lines.extend(f"- {item}" for item in conflicts)
    else:
        md_lines.append("- (none)")

    sources = data.get("sources", [])
    md_lines.extend(["", "## Sources"])
    if sources:
        md_lines.extend(f"- {item}" for item in sources)
    else:
        md_lines.append("- (none)")

    return "\n".join(md_lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate understanding snapshot outputs"
    )
    parser.add_argument("--config", type=str, default="config/understanding.yaml")
    args = parser.parse_args()

    config_path = (ROOT / args.config).resolve()
    if not config_path.exists():
        print(f"config not found: {config_path}", file=sys.stderr)
        return 1
    config = load_config(config_path)

    owner, repo = repo_slug()

    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

    readme_phase = parse_readme_phase(ROOT / "README.md")
    state_info = parse_state(ROOT / config["state_path"])

    expected_phase = config.get("phase")
    conflicts: List[str] = []
    observed_state = state_info.get("phase")
    if expected_phase and readme_phase and expected_phase != readme_phase:
        conflicts.append(
            f"Phase mismatch: expected={expected_phase}, readme={readme_phase}"
        )
    if expected_phase and observed_state and expected_phase != observed_state:
        conflicts.append(
            f"Phase mismatch: expected={expected_phase}, state={observed_state}"
        )

    unknowns: Dict[str, str] = {}

    pr_summaries, pr_error = collect_pr_summaries(owner, repo)
    if pr_error:
        unknowns["prs"] = pr_error
    else:
        pr_summaries = pr_summaries[:5]

    ruleset_reported, ruleset_error = collect_ruleset_contexts(owner, repo)
    if ruleset_error:
        unknowns["rulesets"] = ruleset_error
        ruleset_reported = []

    branch_reported, branch_error = collect_branch_contexts(owner, repo)
    if branch_error:
        unknowns["branch_protection"] = branch_error
        branch_reported = []

    latest = latest_evidence(config["evidence_glob"])
    evidence_entries: List[str] = []
    if latest:
        evidence_entries.append(latest)
    for item in state_info.get("evidence", [])[:3]:
        if item not in evidence_entries:
            evidence_entries.append(item)

    c_section: List[str] = []
    for item in state_info.get("highlights", [])[:5]:
        c_section.append(item)
    for pr in pr_summaries:
        c_section.append(pr)

    delta_section: List[str] = []
    for item in state_info.get("pending", [])[:5]:
        delta_section.append(item)
    if not delta_section:
        delta_section.append("(none observed)")

    next_entries = [
        {
            "title": "Diag自動コメントの追加",
            "dod": "任意PRで required vs reported 差分が自動表示される",
            "reason": "δで観測した理解Diag未導入のギャップを解消する",
        }
    ]

    constraints = {
        "ruleset": {
            "required": config.get("ruleset_required", []),
            "reported": ruleset_reported,
        },
        "branch": {
            "required": config.get("branch_required", []),
            "reported": branch_reported,
        },
    }

    if config.get("ruleset_required"):
        required_set = set(config.get("ruleset_required", []))
        reported_set = set(ruleset_reported)
        missing = sorted(required_set - reported_set)
        extra = sorted(reported_set - required_set)
        constraints["ruleset"]["missing"] = missing
        if extra:
            constraints["ruleset"]["extra"] = extra
    if config.get("branch_required"):
        required_branch = set(config.get("branch_required", []))
        reported_branch = set(branch_reported)
        constraints["branch"]["missing"] = sorted(required_branch - reported_branch)
        extra_branch = sorted(reported_branch - required_branch)
        if extra_branch:
            constraints["branch"]["extra"] = extra_branch

    sources = [
        "README.md",
        config.get("state_path", ""),
    ]
    if latest:
        sources.append(latest)
    for pr in pr_summaries:
        number = re.search(r"PR #(\d+)", pr)
        if number:
            num = number.group(1)
            sources.append(f"https://github.com/{owner}/{repo}/pull/{num}")

    data = {
        "project": config.get("project_id"),
        "timestamp": timestamp,
        "expected": {"phase": expected_phase},
        "observed": {
            "readme": {"phase": readme_phase},
            "state": {"phase": observed_state},
        },
        "conflicts": conflicts,
        "c": c_section,
        "g": config.get("goals", {}),
        "delta": delta_section,
        "constraints": constraints,
        "evidence": evidence_entries,
        "next": next_entries,
        "unknowns": unknowns,
        "sources": sources,
    }

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    base_name = f"uc_{config.get('project_id')}_{timestamp}"
    json_path = reports_dir / f"{base_name}.json"
    md_path = reports_dir / f"{base_name}.md"

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md_path.write_text(build_markdown(data), encoding="utf-8")

    print(str(json_path.relative_to(ROOT)))
    print(str(md_path.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
