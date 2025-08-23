import random
import string
import time


def new_trace_id(prefix="tr"):
    ts = int(time.time() * 1000)
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{ts}-{rand}"
