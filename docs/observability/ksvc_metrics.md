# KService メトリクス収集テンプレ

## 使い方
1. `infra/observability/podmonitor-ksvc.yaml` の `<SERVICE>` と `<NAMESPACE>` を置換して適用。
2. kube-prometheus-stack（release=kps）が `monitoring` NS にあることを確認。
3. `up{namespace="<NAMESPACE>",pod=~"<SERVICE>-.*"}` が `1` になること。
4. Grafana で RPS 等（実在名に合わせる）を1枚パネル化。

## DoD
- Prometheus targets: UP
- `up{…}` = 1
- Grafana: UP or RPS のパネル1枚
