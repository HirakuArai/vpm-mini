"""
core/__init__.py
----------------
* .env から OPENAI_API_KEY を読み込み
* OpenAI クライアントを生成
* ask_openai() で最小チャット呼び出し

※ src/ レイアウトなので、上位レイヤーからは
   `sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))`
   で import してください（CLI や Streamlit 側サンプル参照）。
"""

from dotenv import load_dotenv
from openai import OpenAI
import os
import pathlib

# --- .env を読み込む（絶対パス指定で確実に） ----------------------------
DOTENV_PATH = pathlib.Path("/Users/hiraku/projects/vpm-mini/.env")  # <-- ここを環境に合わせて変更
load_dotenv(DOTENV_PATH, override=True)
# -------------------------------------------------------------------------

# OpenAI クライアント（API キーは環境変数から自動取得）
client = OpenAI()

def ask_openai(obj_id: str, user_msg: str) -> str:
    """
    最小チャットラッパー
    :param obj_id: 目的 ID（現状ではログなどに未使用、今後拡張予定）
    :param user_msg: ユーザ入力
    :return: アシスタントの返答テキスト
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.choices[0].message.content
