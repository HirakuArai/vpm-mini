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
import pathlib
import time
from uuid import uuid4

# --- .env を読み込む（絶対パス指定で確実に） ----------------------------
DOTENV_PATH = pathlib.Path(
    "/Users/hiraku/projects/vpm-mini/.env"
)  # <-- ここを環境に合わせて変更
load_dotenv(DOTENV_PATH, override=True)
# -------------------------------------------------------------------------

# OpenAI クライアント（API キーは環境変数から自動取得）
client = OpenAI()


def get_openai_client() -> OpenAI:
    """Return the shared OpenAI client instance."""
    return client


def ask_openai(obj_id: str, user_msg: str) -> str:
    """
    最小チャットラッパー
    :param obj_id: 目的 ID（現状ではログなどに未使用、今後拡張予定）
    :param user_msg: ユーザ入力
    :return: アシスタントの返答テキスト
    """
    from src.core.logger import append_log

    session_id = str(uuid4())
    msg_id = str(uuid4())
    parent_id = None
    model = "gpt-4o-mini"
    start_ts = time.time()

    # 送信ログ
    append_log(
        {
            "role": "user",
            "content": user_msg,
            "session_id": session_id,
            "msg_id": msg_id,
            "parent_id": parent_id,
            "objective": obj_id or "vpm-mini",
            "channel": "chat-ui",
            "model": model,
        }
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_msg}],
    )

    # 受信ログ
    append_log(
        {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "session_id": session_id,
            "msg_id": str(uuid4()),
            "parent_id": msg_id,
            "objective": obj_id or "vpm-mini",
            "channel": "chat-ui",
            "model": model,
            "tokens_out": response.usage.completion_tokens,
            "elapsed_ms": int((time.time() - start_ts) * 1000),
        }
    )

    return response.choices[0].message.content
