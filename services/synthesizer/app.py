from fastapi import FastAPI, Request
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import time

app = FastAPI()
registry = CollectorRegistry()
REQ = Counter(
    "hello_ai_requests_total",
    "Requests",
    ["route", "method", "code"],
    registry=registry,
)
DUR = Histogram("hello_ai_request_duration_seconds", "Duration", registry=registry)
UP = Gauge("hello_ai_up", "Up", registry=registry)
UP.set(1)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.middleware("http")
async def mw(req: Request, call_next):
    t = time.time()
    resp = await call_next(req)
    REQ.labels(route=req.url.path, method=req.method, code=str(resp.status_code)).inc()
    DUR.observe(time.time() - t)
    return resp


@app.get("/metrics")
def metrics():
    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
