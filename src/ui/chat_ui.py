import sys
import pathlib
import streamlit as st

# --- ① src/ を import パスへ追加 --------------------------
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from core import ask_openai

# ---------------------------------------------------------

st.set_page_config(page_title="vpm-mini Chat", page_icon="💬")

st.title("vpm-mini Chat UI")

# 目的 ID を入力（既定は demo）
obj_id = st.text_input("目的 ID", "demo")

# チャット入力欄（Enter で送信）
user_msg = st.chat_input("メッセージを入力してください…")

if user_msg:
    # ユーザ吹き出し
    st.chat_message("user").write(user_msg)

    # OpenAI から返答を取得
    reply = ask_openai(obj_id, user_msg)

    # アシスタント吹き出し
    st.chat_message("assistant").write(reply)
