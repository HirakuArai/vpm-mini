# Runbook: watcher SLO 初版
## SLO
- p95 <= 1s（5m窓）、Error% <= 1%（5m窓）
## 監視クエリ
- p95: `histogram_quantile(0.95, sum by (le)(rate(hello_ai_request_duration_seconds_bucket{job="watcher"}[5m])))`
- Error%: `(sum(rate(hello_ai_requests_total{job="watcher",code=~"5.."}[5m])) / sum(rate(hello_ai_requests_total{job="watcher"}[5m]))) * 100`
## 典型インシデントと対処
1) p95 悪化: 負荷とPod数の相関/target/requestsの見直し
2) Error率上昇: 5xxのみか/特定routeか、直近デプロイ/依存サービス/RateLimitを確認
## 参照
- Dashboard: 「Hello AI / SLO」
- Rule: infra/k8s/overlays/dev/monitoring/promrule-watcher.yaml
