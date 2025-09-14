import datetime
import re
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, Request
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

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


def _read_state():
    s = Path("STATE/current_state.md").read_text(encoding="utf-8")
    phase = re.search(r"^phase:\s*(.+)", s, re.M)
    phase = phase.group(1).strip() if phase else "UNKNOWN"
    m_c = re.search(r"## 現在地（C）\n([\s\S]*?)(\n## |\Z)", s)
    cur = m_c.group(1).strip().splitlines()[:2] if m_c else []
    m_p5 = re.search(r"## Phase 5:[\s\S]*?\n([\s\S]*?)(\n## |\Z)", s)
    p5 = m_p5.group(1).strip().splitlines()[:3] if m_p5 else []
    return phase, cur, p5


def _latest_reports(n=3):
    try:
        out = (
            subprocess.check_output(
                "ls -1t reports | head -n%d" % n, shell=True, text=True
            )
            .strip()
            .splitlines()
        )
    except Exception:
        out = []
    return [f"reports/{x}" for x in out if x]


@app.get("/api/v1/status_query")
def status_query():
    phase, cur, p5 = _read_state()
    evidence = _latest_reports()
    conclusion = f"現在地: {phase}. 直近: " + (
        " / ".join(cur) if cur else "STATEの『現在地（C）』参照"
    )
    next_steps = ["日次5分レビュー実施（ダッシュボード確認→1改善PR）"]
    confidence = "High" if "Phase 5" in phase else "Med"
    return {
        "conclusion": conclusion,
        "evidence": evidence,
        "next": next_steps,
        "confidence": confidence,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
