"""
Prometheus metrics for hello-ai service
"""

import os
import signal
import time
from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter(
    "hello_ai_requests_total",
    "Total number of HTTP requests",
    ["route", "method", "code"],
)

REQUEST_DURATION = Histogram(
    "hello_ai_request_duration_seconds",
    "Request duration in seconds",
    ["route", "method"],
)

APP_UP = Gauge(
    "hello_ai_up",
    "Application uptime indicator",
)

BUILD_INFO = Info(
    "hello_ai_build_info",
    "Build information",
)

# Initialize metrics
APP_UP.set(1)
BUILD_INFO.info(
    {
        "version": os.getenv("VERSION", "1.0.5"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
    }
)


def metrics_middleware(route_name: str):
    """Decorator for tracking metrics on routes"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = "GET"  # Default for FastAPI routes
            start_time = time.time()

            try:
                response = (
                    await func(*args, **kwargs)
                    if hasattr(func, "__await__")
                    else func(*args, **kwargs)
                )
                status_code = "200"
                REQUEST_COUNT.labels(
                    route=route_name, method=method, code=status_code
                ).inc()
                return response
            except Exception:
                status_code = "500"
                REQUEST_COUNT.labels(
                    route=route_name, method=method, code=status_code
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(route=route_name, method=method).observe(
                    duration
                )

        return wrapper

    return decorator


def get_metrics():
    """Get metrics in Prometheus format"""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def setup_signal_handlers():
    """Setup graceful shutdown handlers"""

    def signal_handler(signum, frame):
        print(f"Received signal {signum}, performing graceful shutdown...")
        # Force flush metrics
        APP_UP.set(0)
        # In a real app, you'd close connections, etc.
        exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
