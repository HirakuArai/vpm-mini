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


st.divider()
st.subheader("意味の理由（寄与トップ±3）")
colA, colB = st.columns(2)
with colA:
    if st.button("Explain δ (理由を表示)"):
        try:
            out = subprocess.check_output(
                ["python3", "scripts/egspace_reason_v1.py"], text=True, timeout=20
            )
            data = json.loads(out)
            if data.get("ok"):
                st.caption(
                    f"embeddings={data.get('embeddings')}  goal={data.get('goal')}"
                )
                st.write("**近づけた（Top+3）**")
                st.json(data.get("closer", []))
                st.write("**遠ざけた（Top-3）**")
                st.json(data.get("farther", []))
                st.write("**δ** = " + str(data.get("stat", {}).get("delta")))
            else:
                st.error("理由計算に失敗: " + str(data))
        except Exception as e:
            st.error(f"reason error: {e}")

with colB:
    st.write("**提案の自動ドラフト（寄与に基づく）**")
    suggestion = st.text_input(
        "Suggested change (1行)", "STATEを更新: 最近のGREEN達成を明記"
    )
    if st.button("寄与ベースの提案をPRにする"):
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rp = pathlib.Path(f"reports/egspace_reason_action_{ts}.md")
        rp.write_text(
            f"# EG-Space reason action {ts}\n- note: {suggestion}\n", encoding="utf-8"
        )
        try:
            # 1) main 直下なら作業ブランチを切る（既に別ブランチならそのまま）
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
            ).strip()
            if branch == "main":
                subprocess.check_call(
                    ["git", "switch", "-c", f"feat/p3-6c-reason-{ts}"]
                )
            # 2) add / commit / push
            subprocess.check_call(["git", "add", str(rp)])
            subprocess.check_call(
                ["git", "commit", "-m", f"feat(p3-6c): egspace reason action {ts}"]
            )
            subprocess.check_call(["git", "push", "-u", "origin", "HEAD"])
            # 3) PR 作成 → 自動マージ
            pr_url = subprocess.check_output(
                [
                    "gh",
                    "pr",
                    "create",
                    "--base",
                    "main",
                    "--title",
                    f"feat(p3-6c): egspace reason action {ts}",
                    "--body",
                    "Auto-created from Demo UI (P3-6c)",
                ],
                text=True,
            ).strip()
            subprocess.run(
                ["gh", "pr", "merge", pr_url.split("/")[-1], "--auto", "--squash"],
                check=False,
            )
            st.success(f"PR created: {pr_url}")
        except Exception as e:
            st.error(f"PR creation failed: {e}")
