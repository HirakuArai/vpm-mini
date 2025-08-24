from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

REQS = Counter("requests_total", "Total requests", ["role"])
JSON_ERR = Counter("json_invalid_total", "Invalid JSON", ["role"])
LAT = Histogram("request_latency_seconds", "Latency seconds", ["role"])


def observe(role, ok=True, start=None):
    REQS.labels(role).inc()
    if not ok:
        JSON_ERR.labels(role).inc()
    if start is not None:
        LAT.labels(role).observe(time.time() - start)


def render_metrics(environ, start_response):
    data = generate_latest()
    start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
    return [data]
