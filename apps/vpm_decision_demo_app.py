import datetime
import json
import os
import re
import sys
import textwrap
from pathlib import Path

import streamlit as st
import yaml

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from core.grounded_answer import grounded_answer
from core.plan_suggester import suggest_plan
from guard.validate_json import validate_answer, validate_plan, validate_state_md

SSOT_STATE = Path("STATE/current_state.md")
REPORTS_DIR = Path("reports")
OUT_DIR = Path("out")
DEMO_DIR = Path("DEMO_SSOT")
EVENTS_DIR = Path("reports/events")
OUT_DIR.mkdir(exist_ok=True)
DEMO_DIR.mkdir(exist_ok=True)
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

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


def _record_validation(kind: str, ok: bool, errors: list[str]) -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {"kind": kind, "ok": bool(ok), "errors": errors}
    path = EVENTS_DIR / f"validation_{timestamp}.yml"
    try:
        path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - logging fallback
        import logging

        logging.getLogger(__name__).warning("Failed to write validation log: %s", exc)


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
    st.markdown("### 検証")
    validate_answer_enabled = st.checkbox("Q&A 検証", value=True)
    validate_plan_enabled = st.checkbox("Plan 検証", value=True)
    validate_state_enabled = st.checkbox("STATE 検証", value=True)

state_text = load_text(SSOT_STATE if use_real else demo_state_path)
facts = parse_state(state_text)
has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
effective_ai = ai_mode_requested and has_openai_key

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 1) 現在地（C/G/δ）")
    st.code(state_text or "(STATE/current_state.md が未作成です)", language="markdown")
    if validate_state_enabled and state_text:
        ok, errors = validate_state_md(state_text)
        _record_validation("state", ok, errors)
        badge = "✅ OK" if ok else "⚠️ NG"
        st.markdown(f"**検証結果:** {badge}")
        if not ok:
            for err in errors:
                st.write(f"- {err}")

with col2:
    st.markdown("### 2) 理解 → 即答（5問）")
    for idx, q in enumerate(FIXED_QUESTIONS):
        with st.expander(q, expanded=False):
            override_key = f"qa_override_{idx}"
            override_rule = st.session_state.get(override_key, False)
            use_ai_flag = effective_ai and not override_rule
            try:
                response = grounded_answer(q, use_ai=use_ai_flag, budget=2000)
            except Exception as exc:  # pragma: no cover - UI path
                st.warning(f"grounded_answer でエラーが発生しました: {exc}")
                response = None
            if response is None:
                continue
            st.json(response)
            if validate_answer_enabled:
                ok, errors = validate_answer(response)
                _record_validation("answer", ok, errors)
                badge = "✅ OK" if ok else "⚠️ NG"
                st.markdown(f"**検証結果:** {badge}")
                if not ok:
                    for err in errors:
                        st.write(f"- {err}")
                    if effective_ai and not override_rule:
                        if st.button("ルール版に差し戻す", key=f"qa_fallback_{idx}"):
                            st.session_state[override_key] = True
                            st.experimental_rerun()
                else:
                    if override_rule:
                        st.session_state.pop(override_key, None)

if free_question.strip():
    st.markdown("### 自由質問")
    override_key = "qa_free_override"
    override_rule = st.session_state.get(override_key, False)
    use_ai_flag = effective_ai and not override_rule
    try:
        free_response = grounded_answer(free_question, use_ai=use_ai_flag, budget=2000)
    except Exception as exc:  # pragma: no cover - UI path
        st.warning(f"自由質問の処理でエラーが発生しました: {exc}")
        free_response = None
    if free_response is not None:
        st.json(free_response)
        if validate_answer_enabled:
            ok, errors = validate_answer(free_response)
            _record_validation("answer", ok, errors)
            badge = "✅ OK" if ok else "⚠️ NG"
            st.markdown(f"**検証結果:** {badge}")
            if not ok:
                for err in errors:
                    st.write(f"- {err}")
                if effective_ai and not override_rule:
                    if st.button("ルール版に差し戻す", key="qa_free_fallback"):
                        st.session_state[override_key] = True
                        st.experimental_rerun()
            else:
                if override_rule:
                    st.session_state.pop(override_key, None)

st.divider()
st.markdown("### 3) 診断 → 優先度（next_actions.json 生成）")
plan_override = st.session_state.get("plan_override", False)
use_ai_plan = effective_ai and not plan_override
try:
    plan_payload = suggest_plan(use_ai=use_ai_plan, limit=5)
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

if validate_plan_enabled:
    ok, errors = validate_plan(plan_payload)
    _record_validation("plan", ok, errors)
    badge = "✅ OK" if ok else "⚠️ NG"
    st.markdown(f"**検証結果:** {badge}")
    if not ok:
        for err in errors:
            st.write(f"- {err}")
        if effective_ai and not plan_override:
            if st.button("ルール版に差し戻す", key="plan_fallback"):
                st.session_state["plan_override"] = True
                st.experimental_rerun()
    else:
        if plan_override:
            st.session_state.pop("plan_override", None)

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
