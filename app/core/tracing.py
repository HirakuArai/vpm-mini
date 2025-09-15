import uuid
import datetime


def gen_trace_id() -> str:
    """tr_<8hex>_YYYYMMDDHHMMSS 形式のトレースIDを払い出し"""
    return f"tr_{uuid.uuid4().hex[:8]}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
