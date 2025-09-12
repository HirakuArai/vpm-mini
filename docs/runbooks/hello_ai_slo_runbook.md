# Runbook: hello-ai SLO 初版

## SLO（初期値）
- p95 latency ≤ 1s（5分移動窓）
- Error rate ≤ 1%（5分移動窓）

## 監視クエリ
- p95: `hello_ai:latency:p95:5m`
- Error %: `hello_ai:error_rate:5m`

## 典型インシデントと対処
### 1) p95 悪化
- 負荷とPod数の相関をGrafanaで確認（QPS/Pod）
- KPA設定の `target`（並行度）・CPU/メモリrequestsを調整
- 影響が大きい場合は一時的に `minScale` を>0へ

### 2) Error率上昇
- 5xxのみか/特定routeかを分解（`{route=~"...",code=~"5.."}`）
- 最近のデプロイ有無を確認、ロールバック手順に従う
- 依存サービス/Secret切替・レート制限の確認

## 参考
- PrometheusRule: `infra/k8s/overlays/dev/monitoring/promrule-hello-ai-slo.yaml`
- ダッシュボード: 「Hello AI / SLO」