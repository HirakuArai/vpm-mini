# P1-7 enable Knative Prometheus metrics & retry (20250908_071416)

- patched config-observability? : true
- queue-proxy sample (/metrics) : revision_app_request_count{...} 10 (from port 9091)
- series(revision_app_request_count): 2
- series(5xx only)             : 0
- targets (hello-ai job)       :
10.244.0.35:9091 up 2025-09-07T22:12:40.704666131Z

- expr (applied to dashboard):
```
sum(rate(revision_app_request_count{response_code_class="5xx"}[5m])) / sum(rate(revision_app_request_count[5m]))
```
- mode      : wired(revision_app_request_count after enable)
- dashboard : grafana/provisioning/dashboards/phase1_kpi.json

## Success!
Successfully enabled Knative Prometheus metrics by:
1. Setting config-observability to use prometheus backend
2. Restarting hello-ai pods to apply configuration  
3. Discovering metrics are available on port 9091 (not 9090)
4. Using correct metric name: revision_app_request_count (not request_count)
5. Dashboard now uses real error rate calculation with Knative metrics
