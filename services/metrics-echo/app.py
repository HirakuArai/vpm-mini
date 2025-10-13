import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


APP_NAME = os.getenv("APP_NAME", "metrics-echo")

app = FastAPI(title=APP_NAME)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "metrics_echo_requests_total",
    "HTTP requests processed",
    ["route", "method", "status"],
)
REQUEST_LATENCY = Histogram(
    "metrics_echo_request_duration_seconds",
    "Latency of HTTP requests in seconds",
)
SERVICE_UP = Gauge(
    "metrics_echo_up",
    "Service availability gauge (1=up)",
)
SERVICE_UP.set(1)


@app.middleware("http")
async def track_http_metrics(request: Request, call_next):
    """Record request counts and latency for each HTTP call."""
    started = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - started

    REQUEST_COUNT.labels(
        route=str(request.url.path),
        method=request.method,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.observe(duration)

    return response


@app.get("/")
async def root():
    return JSONResponse({"service": APP_NAME, "status": "ok"})


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


@app.get("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
