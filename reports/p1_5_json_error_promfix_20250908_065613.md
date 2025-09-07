# P1-5 Prometheus scrape job fix (20250908_065613)

- queue-proxy metrics sample (first pod):
```
Unable to retrieve - binary/gRPC protocol detected at :9090/metrics
```

- series(request_count)                       : 0
- series(request_count{response_code=~"5.."}) : 0
- prometheus targets (hello-ai job):
```
kubernetes-pods-knative-hello-ai 10.244.0.33:9090 down 2025-09-07T21:49:46.454059793Z
Last error: expected a valid start token, got "*" ("INVALID") while parsing: "*"
```

- expr (applied to dashboard):
```
vector(0)
```
- mode      : placeholder(still no request_count - target down)
- dashboard : grafana/provisioning/dashboards/phase1_kpi.json
- config    : infra/k8s/overlays/dev/monitoring/prometheus.yaml

## Analysis
The queue-proxy container at port 9090 is returning binary/gRPC data instead of text-based Prometheus metrics format.
This indicates the metrics endpoint may not be properly configured for Prometheus scraping in the current Knative setup.
