#!/usr/bin/env python3
import argparse
import datetime
import pathlib
import re
import sys

REQ_KEYS = [
    "active_repo",
    "active_branch",
    "phase",
    "context_header",
    "short_goal",
    "exit_criteria",
    "優先タスク",
]


def read_text(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


def extract_sections(md: str):
    # 粗いが堅牢な抽出：key: value 形式と見出し下の箇条書き双方を許容
    found = {}
    for k in REQ_KEYS:
        # key: value 行
        m = re.search(rf"^{re.escape(k)}\s*:\s*(.+)$", md, re.MULTILINE)
        if m:
            found[k] = m.group(1).strip()
            print(f"[extract] {k}: {m.group(1).strip()[:50]}...", file=sys.stderr)
            continue
        # 見出し版（例：## 優先タスク の箇条書き）
        m2 = re.search(rf"^#+\s*{re.escape(k)}[^\n]*\n((?:- .+\n?)+)", md, re.MULTILINE)
        if m2:
            items = [
                line[2:].strip()
                for line in m2.group(1).strip().splitlines()
                if line.startswith("- ")
            ]
            found[k] = items
            print(f"[extract] {k}: {len(items)} items", file=sys.stderr)
    return found


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def main():
    ap = argparse.ArgumentParser(description="Generate C/G/δ view from STATE")
    ap.add_argument(
        "--in",
        dest="inp",
        default="STATE/current_state.md",
        help="Input STATE file (default: STATE/current_state.md)",
    )
    ap.add_argument(
        "--out",
        dest="outp",
        default=None,
        help="Output file (default: reports/p2_state_view_YYYYMMDD_HHMM.md)",
    )
    args = ap.parse_args()

    src = pathlib.Path(args.inp)
    if not src.exists():
        print(f"[state-view] missing file: {src}", file=sys.stderr)
        sys.exit(1)

    print(f"[state-view] reading: {src}", file=sys.stderr)
    md = read_text(src)
    print(
        f"[state-view] file size: {len(md)} chars, {len(md.splitlines())} lines",
        file=sys.stderr,
    )

    data = extract_sections(md)

    missing = [k for k in REQ_KEYS if k not in data or data[k] in (None, "", [])]
    if missing:
        print(f"[state-view] missing keys: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    outp = (
        pathlib.Path(args.outp)
        if args.outp
        else pathlib.Path(f"reports/p2_state_view_{now}.md")
    )

    # Ensure reports directory exists
    outp.parent.mkdir(parents=True, exist_ok=True)

    # 現在地 (C)
    C = [
        f"- repo: `{data['active_repo']}`",
        f"- branch: `{data['active_branch']}`",
        f"- phase: **{data['phase']}**",
        f"- context: {data['context_header']}",
    ]

    # ゴール (G)
    G = [
        f"- short_goal: {data['short_goal']}",
        "- exit_criteria:",
    ] + [f"  - {x}" for x in as_list(data["exit_criteria"])]

    # 優先タスク取得
    tasks = as_list(data["優先タスク"])

    # 差分 (δ)
    delta_lines = [
        "- 未達Exitの補充・検証を優先",
        "- 優先タスクを先頭から実行し証跡化",
    ][:2]

    # 次アクション（最大3件）
    next_actions = [f"- {t}" for t in tasks[:3]] or ["- （未定義）"]

    # 出力構成
    out_md = "\n".join(
        [
            "# 現在地 (C)",
            *C,
            "",
            "# ゴール (G)",
            *G,
            "",
            "# 差分 (δ)",
            *delta_lines,
            "",
            "# 次アクション（最大3件）",
            *next_actions,
            "",
            "---",
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source: {src}",
            f"Total tasks: {len(tasks)}",
        ]
    )

    outp.write_text(out_md, encoding="utf-8")
    print(f"[state-view] written: {outp} ({len(out_md)} chars)", file=sys.stderr)
    print(f"[state-view] extracted keys: {', '.join(data.keys())}", file=sys.stderr)


if __name__ == "__main__":
    main()
