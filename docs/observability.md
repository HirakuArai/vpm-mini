# Observability Index
- ダッシュボード: 「Hello AI / SLO」
- 主要クエリ:
  - p95: histogram_quantile(0.95, sum by (le)(rate(hello_ai_request_duration_seconds_bucket[5m])))
  - Error%: (sum(rate(hello_ai_requests_total{code=~"5.."}[5m])) / sum(rate(hello_ai_requests_total[5m]))) * 100
- 監視: ServiceMonitor targets up==1 / Alerts（Down/Latency/Error）
