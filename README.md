**Dev URL (kind/8080):** `make hello-health` → 200 OK

> 📎 Attachments: `docs/attachments_index.md`（ChatGPT の添付はこの1枚に集約）

# vpm-mini

**context_header:** repo=vpm-mini / branch=main / phase=Phase 2

## Phase 6 (Current)

- Phase 5 完了: `phase5-complete`（GitOps / Canary / Guard / Failover / 800 RPS）
- Phase 6 目標: マルチクラスタのグローバル配信 + 30日連続 SLO 99.9%
- 運用ルール: 1PR=1ステップ=1スナップショット / Auto-merge / タグ

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

## Phase 3 完了 → Phase 4 移行

✅ **Phase 3: 監査 & セキュリティ** 完了 (tag: `phase3-complete`)
- SPIFFE/SPIRE による workload identity 確立
- OPA Gatekeeper によるポリシー強制
- W3C PROV 決定ログ（Ed25519 署名付き S3 保存）
- Chaos エンジニアリング（99% SLO 維持確認）

🚀 **Phase 4: 大規模 Swarm β** 開始
- Istio + Gateway API による高度ルーティング足場
- ArgoCD GitOps デプロイメント基盤
- A/B テスト評価枠組み構築
- 800 cells/sec 大規模負荷耐性確立
- SSOT（運用ループの全体図）: `diagrams/src/ops_single_source_of_truth_v1.md`
- ドキュメント目次: `docs/README.md`

## Quick Start (Trial)
1. フォームで `title/detail/project_id/priority` を投稿
2. `status_query` で C/G/δ/Next を取得
3. 日次5分: ダッシュボード→1改善PR（Evidence必須）

- project_id: `vpm-core`
- decision template: 結論 / 根拠（出典+時刻） / 次の一手 / 信頼度
- scope: STATE / reports / PR(DoD) / Prometheus（意味軸/RAGなし）

### Trial Daily (5分レビュー)
```
make trial-daily
```
- KService / PR / Targets / Alerts を表示
- `reports/daily_status_*.md` にEvidence保存

---
chore: trigger PR Validate (k8s-validate / knative-ready / evidence-dod) for ruleset calibration.


