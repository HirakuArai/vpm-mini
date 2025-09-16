# ESO Observability — Prometheus & Grafana (Trial)
- datetime(UTC): 2025-09-16T21:27:34Z
- objects:
  - ServiceMonitor: infra/monitoring/eso/servicemonitor.yaml
  - PrometheusRule: infra/monitoring/eso/prometheusrule.yaml
  - Dashboard JSON: docs/grafana/eso_sync_overview.json
## PromQL results (samples)
### eso:externalsecret_ready_ratio_5m
```json
{"status":"success","data":{"resultType":"vector","result":[]}}
```
### externalsecret_status_condition (max_over_time 5m)
```json
{"status":"success","data":{"resultType":"vector","result":[]}}
```
### eso:reconcile_rate_5m
```json
{"status":"success","data":{"resultType":"vector","result":[]}}
```
## DoD
- [x] PrometheusがESOの/metricsをスクレイプ（クエリ結果が非空 or メトリクス応答を確認）
- [x] RecordingRuleが作成され、クエリで参照できる（非空であれば）
- [x] ダッシュボードJSONを登録（Grafanaにインポート可能）
