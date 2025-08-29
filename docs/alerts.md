# Alerts (SLO 99.9%)

| Alert | 窓 | Burn rate 目安 | Severity | 概要 |
|---|---:|---:|---|---|
| **SLOFastBurn**  | 5m  | ≈14.4x | page   | 急速消費（2時間で枯渇相当） |
| **SLOSlowBurn**  | 30m | ≈6x    | ticket | 漸進消費（数日で枯渇相当） |
| **SLOTrendWarn** | 1h  | ≈3x    | warn   | トレンド警告（注意喚起） |

- **Runbook**: `docs/runbooks/http_slo_999.md`  
- **Alertmanager（dev）**: Webhook ロガー/コンソール  
- **Alertmanager（prod）**: Slack/Oncall/Pager などへルーティング
