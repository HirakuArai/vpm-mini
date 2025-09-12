from fastapi import FastAPI
from metrics import get_metrics, metrics_middleware, setup_signal_handlers
import threading
from prometheus_client import start_http_server

app = FastAPI()

# Setup signal handlers for graceful shutdown
setup_signal_handlers()


# Start metrics server on port 9090
def start_metrics_server():
    try:
        start_http_server(9090)
        print("Metrics server started on port 9090")
    except Exception as e:
        print(f"Failed to start metrics server: {e}")


# Start metrics server in background thread
threading.Thread(target=start_metrics_server, daemon=True).start()


@app.get("/")
@metrics_middleware("root")
def root():
    return {"message": "hello-ai from vpm-mini"}


@app.get("/healthz")
@metrics_middleware("healthz")
def healthz():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    return get_metrics()
