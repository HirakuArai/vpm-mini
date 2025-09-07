# P1 KPI GREEN — evidence

- p50 latency:
histogram_quantile(0.5, sum by (le)(rate(prometheus_http_request_duration_seconds_bucket[5m])))

- JSON error rate:
sum(rate(revision_app_request_count{response_code_class="5xx"}[5m])) / sum(rate(revision_app_request_count[5m]))

- ROUGE-L:
vmp_rouge_l_score

- datasource: prom-k8s (http://prometheus.monitoring.svc:9090)
