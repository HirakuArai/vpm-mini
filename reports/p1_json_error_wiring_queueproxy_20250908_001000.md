# P1-5 JSON error via Knative queue-proxy (20250908_001000)
- ksvc annotated : hyper-swarm/hello-ai (scrape=:9090/metrics)
- series(request_count)                     : 0
- series(request_count{response_code=~"5.."}) : 0
- expr:
```
vector(0)
```
- dashboard : grafana/provisioning/dashboards/phase1_kpi.json
- datasource: prom-k8s
- mode      : placeholder(no request_count yet)
