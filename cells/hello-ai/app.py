import os
import time
import uuid
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # ライブラリ未導入でも起動だけはできるように

app = FastAPI()

# Knative は $PORT を渡す
PORT = int(os.getenv("PORT", "8080"))


def get_client():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/hello-ai", response_class=PlainTextResponse)
def hello_ai(msg: str = "ping"):
    rid = str(uuid.uuid4())
    t0 = time.time()
    ai_enabled = os.getenv("AI_ENABLED", "false").lower() == "true"
    model = os.getenv("MODEL", "gpt-4.1-mini")
    max_tokens = int(os.getenv("MAX_TOKENS", "64"))
    timeout_ms = int(os.getenv("TIMEOUT_MS", "2000"))

    text = f"(mock) hello: {msg}"
    fb = "true"

    if ai_enabled:
        client = get_client()
        if client:
            try:
                r = client.responses.create(
                    model=model,
                    input=f"Reply shortly to: {msg}",
                    max_output_tokens=max_tokens,
                    timeout=timeout_ms / 1000.0,
                )
                # OpenAI 1.x のシンプルな取り出し
                text = getattr(r, "output_text", "").strip() or "(fallback) hello"
                fb = "false" if text and text != "(fallback) hello" else "true"
            except Exception:
                text = "(fallback) hello"
                fb = "true"
        else:
            # キー未設定／ライブラリなし
            text = "(fallback) hello"
            fb = "true"

    dur = int((time.time() - t0) * 1000)
    headers = {"X-Trace-Id": rid, "X-Dur-Ms": str(dur), "X-Fallback": fb}
    return Response(content=text, media_type="text/plain", headers=headers)
