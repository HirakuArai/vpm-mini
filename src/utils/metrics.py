import http.server
import os
import socketserver
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Metrics
REQS = Counter("requests_total", "Total requests", ["role"])
JSON_ERR = Counter("json_invalid_total", "Invalid JSON", ["role"])
LAT = Histogram("request_latency_seconds", "Latency seconds", ["role"])


class MetricsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        else:
            self.send_response(404)
            self.end_headers()


def serve_metrics():
    """Serve Prometheus metrics on METRICS_PORT."""
    port = int(os.getenv("METRICS_PORT", "9000"))
    handler = MetricsHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[metrics] serving on port {port}")
        httpd.serve_forever()


if __name__ == "__main__":
    serve_metrics()
