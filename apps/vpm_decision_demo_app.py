import datetime
import json
import os
import re
import sys
import textwrap
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from core.grounded_answer import grounded_answer
from core.plan_suggester import suggest_plan

SSOT_STATE = Path("STATE/current_state.md")
REPORTS_DIR = Path("reports")
OUT_DIR = Path("out")
DEMO_DIR = Path("DEMO_SSOT")
OUT_DIR.mkdir(exist_ok=True)
DEMO_DIR.mkdir(exist_ok=True)

FIXED_QUESTIONS = [
    "今のPhaseと短期ゴールは？",
    "P2-2のExit Criteriaは満たされている？根拠は？",
    "次に着手すべきタスクは？根拠（C/G/δ）も添えて。",
    "失敗時のロールバック手順は？",
    "今日のデモをEvidenceとして残すには？",
]


def load_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def ensure_demo_state() -> Path:
    demo_state = DEMO_DIR / "current_state.md"
    if demo_state.exists():
        return demo_state
    demo_state.write_text(
        textwrap.dedent(
            """
            # === Current State (DEMO) ===
            context_header: "repo=vpm-mini / branch=main / phase=Phase 2"

            ## 現在地（C）
            - Phase 2 後半：Knative足場と観測ラインが稼働

            ## ゴール（G）
            - P2-2: Hello KService READY=True（疎通・証跡）

            ## δ（差分）
            - hello-ksvc manifest検証
            - kourier経由の疎通（Host指定で200）
            - reports/ にEvidenceを保存
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return demo_state


def parse_state(md: str) -> dict:
    phase_match = re.search(r"phase=([^\s\"]+)", md)
    short_goal_match = re.search(r"P2-2.*READY=True", md)
    delta_section = re.search(r"##\s*δ[^#]*", md, re.S)
    deltas = []
    if delta_section:
        deltas = re.findall(r"-\s*(.+)", delta_section.group(0))
    return {
        "phase": phase_match.group(1) if phase_match else "Phase ?",
        "short_goal": (
            short_goal_match.group(0) if short_goal_match else "短期ゴール未記載"
        ),
        "delta": deltas,
    }


def next_actions(facts: dict) -> list[dict]:
    return [
        {
            "id": "P2-2.a",
            "title": "hello-ksvc apply",
            "priority": 1,
            "DoD": ["READY=True", "reports/にMD作成"],
            "risk": "低",
        },
        {
            "id": "P2-2.b",
            "title": "kourier疎通確認（Host指定で200）",
            "priority": 2,
            "DoD": ["curl 200", "ログ保存"],
            "risk": "中",
        },
        {
            "id": "P2-2.c",
            "title": "Evidence作成（MD/PNG）",
            "priority": 3,
            "DoD": ["reports/*.md", "reports/img/*.png"],
            "risk": "低",
        },
    ]


def pr_draft(selected: dict, facts: dict) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return textwrap.dedent(
        f"""
        # PR: {selected['title']}（{facts['phase']}）
        ## 背景（C/G/δ）
        - C: Phase={facts['phase']}
        - G: {facts['short_goal']}
        - δ: {', '.join(facts['delta']) or '（記載なし）'}

        ## 変更点
        - {selected['title']}

        ## DoD
        {chr(10).join(f'- [ ] {item}' for item in selected['DoD'])}

        ## Evidence
        - reports/（MD/PNG）に保存
        - 実行時刻: {ts}

        ## Rollback
        - manifest を前タグへ戻し、PR で証跡化
        """
    ).strip()


# ---------------- Streamlit UI -----------------
st.set_page_config(page_title="VPM Decision Demo", layout="wide")
st.title("VPM Decision Demo – 理解 → 優先度 → PR草案")

demo_state_path = ensure_demo_state()

with st.sidebar:
    st.subheader("SSOT Paths")
    st.write("STATE:", SSOT_STATE if SSOT_STATE.exists() else demo_state_path)
    st.write("reports:", REPORTS_DIR if REPORTS_DIR.exists() else DEMO_DIR / "reports")
    use_real = st.checkbox("実リポのSSOTを使う（存在する場合）", value=True)
    st.markdown("### AI モード")
    ai_mode_requested = st.checkbox("AIモード (OPENAI_API_KEY 必須)", value=False)
    free_question = st.text_input("自由質問", "")
    if ai_mode_requested and not os.getenv("OPENAI_API_KEY"):
        st.info("OPENAI_API_KEY が未設定のためルール回答で動作します。")

state_text = load_text(SSOT_STATE if use_real else demo_state_path)
facts = parse_state(state_text)
has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
effective_ai = ai_mode_requested and has_openai_key

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 1) 現在地（C/G/δ）")
    st.code(state_text or "(STATE/current_state.md が未作成です)", language="markdown")

with col2:
    st.markdown("### 2) 理解 → 即答（5問）")
    for q in FIXED_QUESTIONS:
        with st.expander(q, expanded=False):
            try:
                response = grounded_answer(q, use_ai=effective_ai, budget=2000)
            except Exception as exc:  # pragma: no cover - UI path
                st.warning(f"grounded_answer でエラーが発生しました: {exc}")
            else:
                st.json(response)

if free_question.strip():
    st.markdown("### 自由質問")
    try:
        free_response = grounded_answer(free_question, use_ai=effective_ai, budget=2000)
    except Exception as exc:  # pragma: no cover - UI path
        st.warning(f"自由質問の処理でエラーが発生しました: {exc}")
    else:
        st.json(free_response)

st.divider()
st.markdown("### 3) 診断 → 優先度（next_actions.json 生成）")
try:
    plan_payload = suggest_plan(use_ai=effective_ai, limit=5)
except Exception as exc:  # pragma: no cover - defensive path
    st.warning(f"plan_suggester でエラーが発生しました: {exc}")
    plan_payload = {"next_actions": [], "short_goal": facts["short_goal"]}

if not plan_payload.get("short_goal"):
    plan_payload["short_goal"] = facts["short_goal"]

actions = plan_payload.get("next_actions", [])
plan_json = json.dumps(plan_payload, ensure_ascii=False, indent=2)
st.code(plan_json, language="json")
plan_path = OUT_DIR / "next_actions.json"
plan_path.parent.mkdir(parents=True, exist_ok=True)
plan_path.write_text(plan_json, encoding="utf-8")
st.success(f"Saved: {plan_path}")

st.divider()
st.markdown("### 4) 提案 → アクション（PR草案生成）")
if actions:
    options = {f"{a['id']} – {a['title']}": a for a in actions}
    choice = st.selectbox("アクションを選択", list(options.keys()))
    selected = options[choice]
    draft = pr_draft(selected, facts)
    st.code(draft, language="markdown")
    (OUT_DIR / "pr_draft.md").write_text(draft, encoding="utf-8")
    st.success(f"Saved: {OUT_DIR / 'pr_draft.md'}")
else:
    st.info("候補がありません。STATE/current_state.md に δ を記載してください。")

st.caption(
    "※デモ用の最小UIです。実運用では認証/CI連携/権限管理などを追加してください。"
)
