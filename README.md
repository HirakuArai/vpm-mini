# vpm-mini

## Quickstart (10min Repro, Phase 1)
```bash
git clone https://github.com/HirakuArai/vpm-mini.git
cd vpm-mini
make compose-up
# wait ~10s
curl -fsS http://localhost:8001/healthz
curl -fsS http://localhost:9090/api/v1/targets | jq .
open http://localhost:3000  # (admin/admin)
```

## Phase 1 完了 (S1–S10)

✅ **Docker Compose 化** (5 Roles: watcher, curator, planner, synthesizer, archivist)

✅ **Redis 統合**

✅ **HTTP /healthz エンドポイント**

✅ **trace_id クロスロール伝播**

✅ **Prometheus メトリクス** (/metrics)

✅ **Prometheus サーバ統合** (9090)

✅ **Grafana ダッシュボード** (3000)
- JSON error rate
- p50 latency  
- ROUGE-L score

✅ **ROUGE-L Exporter 実装** (/metrics に反映)

## Evidence
- `reports/snap_phase1_healthz.txt` – 全ロール "ok"
- `reports/snap_phase1_targets.json` – Prometheus 全ターゲット UP
- `reports/snap_phase1_query_up.json` – up=1 確認
- `reports/snap_phase1_compose_ps.txt` – 全8サービス Healthy

## Next
**Phase 2 Kickoff**: kind + Knative 足場構築