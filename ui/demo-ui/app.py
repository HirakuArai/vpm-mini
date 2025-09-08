import json
import subprocess
import pathlib
import streamlit as st
from datetime import datetime, timezone

st.set_page_config(page_title="Feature-Confirmation Demo v1", layout="wide")
st.title("Feature-Confirmation Demo v1")

proj = st.text_input("Project name", "vpm-mini")
txt = st.text_area("New note (append to memory.json)", "", height=120)

c1, c2 = st.columns(2)
with c1:
    if st.button("メモを送信"):
        p = pathlib.Path("memory.json")
        try:
            mem = json.load(open(p, "r", encoding="utf-8"))
        except Exception:
            mem = []
        mem.insert(
            0,
            {
                "created_at": datetime.now(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
                "role": "user",
                "text": txt.strip(),
            },
        )
        json.dump(mem, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        st.success("Appended to memory.json")
with c2:
    if st.button("δ を計算"):
        out = subprocess.check_output(["python3", "scripts/egspace_min.py"], text=True)
        st.json(json.loads(out))

st.divider()
st.subheader("提案 → PR 作成（STATEへ反映）")
suggest = st.text_input("Proposal (1行)", "記録: Demo v1 実行")
if st.button("この提案でPR作成"):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rp = pathlib.Path(f"reports/demo_v1_{ts}.md")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(
        f"# Demo v1 report {ts}\n- project: {proj}\n- note: {suggest}\n",
        encoding="utf-8",
    )
    pr_url = subprocess.check_output(
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--title",
            f"demo: {proj} v1 ({ts})",
            "--body",
            "Demo v1 auto-generated PR",
        ],
        text=True,
    ).strip()
    subprocess.run(["gh", "pr", "merge", pr_url.split("/")[-1], "--auto", "--squash"])
    st.success(f"PR created: {pr_url}")
