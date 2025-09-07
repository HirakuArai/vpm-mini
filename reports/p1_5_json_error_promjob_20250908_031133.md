# P1-5 JSON error wiring via Prometheus scrape job (20250908_031133)

- added scrape job  : kubernetes-pods-knative-hello-ai
- series(request_count)                       : 0
- series(request_count{response_code=~"5.."}) : 0
- expr:
```
vector(0)
```
- dashboard : grafana/provisioning/dashboards/phase1_kpi.json
- datasource: prom-k8s
- mode      : placeholder(no request_count yet)
