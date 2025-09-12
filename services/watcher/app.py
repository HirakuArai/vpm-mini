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

app = FastAPI(title="watcher")

registry = CollectorRegistry()
REQ_TOTAL = Counter(
    "hello_ai_requests_total",
    "Requests",
    ["route", "method", "code"],
    registry=registry,
)
DUR = Histogram("hello_ai_request_duration_seconds", "Req duration", registry=registry)
UP = Gauge("hello_ai_up", "Up", registry=registry)
UP.set(1)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    start = time.time()
    resp = await call_next(request)
    REQ_TOTAL.labels(
        route=request.url.path, method=request.method, code=str(resp.status_code)
    ).inc()
    DUR.observe(time.time() - start)
    return resp


@app.get("/metrics")
def metrics():
    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
