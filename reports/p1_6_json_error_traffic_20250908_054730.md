# P1-6 JSON error traffic & switch (20250908_054730)
- ksvc URL : http://hello-ai.hyper-swarm.127.0.0.1.sslip.io
- series(request_count)                     : 0
- series(request_count{response_code=~"5.."}) : 0
- expr (applied to dashboard):
```
vector(0)
```
- mode: placeholder(still no request_count)
- dashboard: grafana/provisioning/dashboards/phase1_kpi.json
