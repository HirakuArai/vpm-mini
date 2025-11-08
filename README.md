**Dev URL (kind/8080):** `make hello-health` → 200 OK

> 📎 Attachments: `docs/attachments_index.md`（ChatGPT の添付はこの1枚に集約）

# vpm-mini

**context_header:** repo=vpm-mini / branch=main / phase=Phase 2

## Phase 2

- Current: dev 監視ラインの整備と理解Diagの導入（Phase 2）
- 運用ルール: 1PR=1ステップ=1スナップショット / Auto-merge / タグ

## Execution Model
- **唯一の実行器**: devbox Codex（常駐ワーカー）
- **Atlas**: OpenAIエージェントブラウザ。Cloud Shell や GitHub UI の操作補助のみ（実行はしない）
- **Run-Contract(JSON)**: すべての実行は JSON 契約で記述し、`reports/` に証跡を集約

## Provision devbox VM
- Trigger `.github/workflows/provision_devbox.yml` manually (uses GCP WIF + `GCP_WIF_PROVIDER` / `GCP_SA_EMAIL` secrets)
- Defaults: project `vpm-mini-prod`, zone `asia-northeast1-b`, VM name `devbox-codex`
- Post-create steps (SSH, bootstrap, PAT, worker verify) are captured in `docs/ops/devbox_vm.md`

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


### Understanding Guard (post)
- 既存guardは保持。本workflowはPR上のコメント/ラベル/Evidence整形のみ（非ブロッキング）
- GH_TOKEN を明示し、PR文脈が無いときは動作をスキップ

### P3-3 Exit (non-blocking guard stabilized)
- 🧭 一意コメント＋warnラベル＋Evidence生成（post）
- legacy guard は continue-on-error で非ブロッキング運用
- 詳細: reports/p3_3_exit_20251004T001113Z.md

### P3-4 Kickoff
- Add dry-run workflow to emit success statuses for future required checks:
  - understanding/guard-required, understanding/snapshot-present, understanding/goals-synced
- No rule change yet; observe impact while keeping post workflow.

## Kourier Access (dev)

```bash
make -f Makefile.kourier curl-hello      # NodePort優先でHTTP 200確認
make -f Makefile.kourier pf-kourier      # 8080:8080 port-forwardを起動（別ターミナルで curl-hello-pf）
make -f Makefile.kourier curl-hello-pf   # 強制的にpf経由でHTTP 200確認
```

## VPM Decision Demo (Streamlit)

```bash
pip install -r requirements-demo.txt
streamlit run apps/vpm_decision_demo_app.py
```

## Evidence Render
- Manual: push to `manual-render` (set `from`/`to` in commit message)
- Daily: 07:00 JST via `render_cron.yml`
- Runbook: ops/runbook.md (updated 2025-10-22T20:51:43Z)
