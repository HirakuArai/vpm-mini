# === State Declaration (Single Source of Truth) ===
active_repo: vpm-mini
active_branch: main
phase: Phase 5: Scaling & Migration
context_header: "repo=vpm-mini / branch=main / phase=Phase 5: Scaling & Migration"
short_goal: "Knative Autoscaling + SLO formalization + First Compose service migration"
exit_criteria:
  - "P5-1 GREEN: Knative Autoscaling (HPA/KPA) with scale-to-zero demonstrated"
  - "P5-2 GREEN: SLO targets defined and measured with runbooks"
  - "P5-3 GREEN: At least one Compose service successfully migrated to Knative"
updated_at: 2025-09-15T00:00:00Z

---

## この文書の役割
本プロジェクトは、事象目的空間における **現在地（C）**、**ゴール（G）**、差分 **δ** を常に明示し、次の一手を機械的に判断できるようにする。ここでは **唯一の前提（SSOT）** を宣言する。

## プロジェクト最終目的
**Hyper-Swarm / VPM** を構築し、複数AIエージェントの連携により **常時自己進化型の開発運用基盤** を確立する。

## フェーズ構成と現在地
- **Phase 0**：ローカル venv で 5ロール（対話→要約→プラン→エコー）一周の証跡化
- **Phase 1**：Compose + 監視土台（完了）
- **Phase 2（←現在地）**：kind + Knative（v1.18）足場 → Hello KService `READY=True / HTTP 200` の証跡化
- 以降：サービス移植・Autoscale・観測ラインのK8s移行

## 現在地（C）
- Phase 1 までの環境は main で安定
- #128 により **Evidence Check（PR本文↔差分の不整合検知）** 導入済み
- `.ops/deploy_freeze.json` は **true 維持**（不要なCDを抑止）
- **欠落**：Phase 0 サニティ（5ロール一周の実行証跡）／ Phase 2 `hello-ksvc` READY 証跡

## ゴール（G）— Phase 2 Kickoff 達成
- **P2-1**: `scripts/p2_bootstrap_kind_knative.sh` で kind + Knative v1.18 を冪等構築
- **P2-2**: `infra/k8s/overlays/dev/hello-ksvc.yaml` を適用し  
  `kubectl get ksvc hello` → `READY=True`、`curl` 応答 → `HTTP 200` の証跡を `reports/` に保存

## 差分（δ：方向と距離）
- 距離：Phase 0 サニティ + Phase 2 READY 証跡が未充足
- 方向：**器（CI/観測）より中身（実行対象とAI駆動サイクル）を先に**。P2-1 → P2-2 → #125 再開

## 優先タスク（直近の順序）
1. **Phase 0 サニティ**：ローカルで 5ロール一周 → `make test` Green → ログ/JSON証跡コミット
2. **P2-1 / P2-2**：kind + Knative 足場構築 → `hello-ksvc` READY & HTTP 200 証跡化
3. **#125 観測ライン拡張**：READY 達成後に Pushgateway / Grafana をKnativeへ

## 決定（2025-09-02）
- 「本質的処理（AI中心の5ロール循環・READYなKService）」が未実証であったため、**Phase 0 / 2 へ立ち戻って証跡を先に揃える**。Freeze は READY 証跡が揃ったタイミングで解除し、#125 を進める。
### Phase 2 Kickoff – P2-1 足場構築（kind + Knative v1.18）
- Status: **GREEN**
- Evidence: `reports/p2_1_bootstrap_20250903_045206.md`
- Decision Log:
  - kind クラスタを作成（既存時は再利用）
  - Knative Serving v1.18 + net-kourier を適用
  - `ingress.class = kourier` / `config-domain = 127.0.0.1.sslip.io` を設定
  - `knative-serving` / `kourier-system` の全 Deploy が Available を確認

### Phase 2 – P2-2 Hello-AI（Knative Service）
- Status: **GREEN**
- Evidence: `reports/p2_2_ai_enabled_success.md` / `reports/p2_2_openai_proof_20250903_125848.json`
- Decision Log:
  - 画像を `ko.local/hello-ai:dev` に固定（tag-resolve skip + kind load）
  - .env の `OPENAI_API_KEY` を Secret 取り込み
  - `AI_ENABLED=true` で 200 応答・**X-Fallback:false** を確認（Pod内実コール: `reports/p2_2_openai_proof_20250903_125848.json`）

#### Phase 2 – P2-3 CI/SSOT 結線（着手）
- 追加: k8s-manifests-validate（kubectl --dry-run=client）+ reports/*.json Artifact

### Phase 2 – P2-4 Observability（最小）
- Status: **GREEN**
- Evidence: `reports/p2_4_obs_20250903_140653.json`
- Decision Log:
  - hello-ai を N=12 回呼び出し、`X-Dur-Ms` と `X-Fallback` を集計（p50/p95/avg）
  - 結果: 12/12 成功、fallback_false=12、p50=974ms、p95=3543ms

### Phase 2 – P2-5 Hardening（最小）
- Status: **GREEN**
- Evidence: `reports/p2_5_failpaths_20250903_143833.json`
- Decision Log:
  - invalid_key / ai_disabled / invalid_model の3系統で **外形200 + X-Fallback:true** を確認
  - 全ケース成功 (3/3 PASS) - graceful fallback動作確認済み

### Phase 2 – P2-6 Snapshot & Tag
- Status: **GREEN**
- Evidence: `reports/p2_6_snapshot_20250903_150554.md`
- Decision Log:
  - Phase 2（P2-1..P2-5）の証跡を集約し、タグで復元ポイントを作成
  - Evidence: 15件のレポートファイル（bootstrap/AI/CI/obs/hardening）

### Course Correction Log – Phase 0/2 回帰（本質稼働の証跡確保）
- 背景: 計器先行により Phase 5 相当に見えていたが、Phase 0/2 の証跡が欠落
- 判断: Phase 0 サニティ → Phase 2 の **縦スライス** を先に通す方針へ切替
- 実施: **P2-1..P2-6** を完了し、タグ `p2-vs-complete-20250903` を付与（復元点）
- Evidence: `reports/retro_phase2_course_correction_20250903_153645.md`
- P0 semantics sanity ✅（10 samples / human OK / source-anchored v2） — 2025-09-05
- P0 semantics sanity ✅（30 samples / human OK / source-anchored v2） — 2025-09-05
- P3-1 Gatekeeper ✅（allowed-repos + no-latest、DENY証跡あり、hello-ai READY=True） — 2025-09-05
- P3-2.1 SPIRE 最小導入 ✅（server/agent 稼働・証跡あり） — 2025-09-07
- P3-2.2 hello-ai SVID 付与 ✅（SPIFFE ID 設定・evidenceあり） — 2025-09-07
- P3-2.3 PROV 決定ログ（最小） ✅（reports/prov_*.jsonld 生成・証跡あり） — 2025-09-07
- P3-2.4 PROV 決定ログ（拡張） ✅（reports/prov_p3_2_4_*.jsonld 生成・証跡あり） — 2025-09-07
- P1-3 Grafana K8s datasource ✅（prom-k8s 追加・p50 panel 連携・証跡あり） — 2025-09-07
- P1 KPI 基盤 ✅（p50=Prometheus実配線、JSON error rate=revision_app_request_count 実配線、ROUGE-L=vpm_rouge_l_score） — 2025-09-08
- P3-3 Chaos（pod-kill最小） ✅（Ready=True継続／p50≈0.05s／証跡あり） — 2025-09-08
- P2 最小オートスケール ✅（1→3 pods / 200並行×120s / p50≈0.05s / 証跡あり） — 2025-09-08
- P2 コールドスタート ✅（cold≈84ms / warm≈16ms / 証跡あり） — 2025-09-08
- Demo v1 ✅（UI→EG-Space→PR 自動反映） — 2025-09-08
- P3-6 EG-Space v1 ✅（寄与±3表示・提案PR・pgvector/embeddings 稼働） — 2025-09-09
status: P4-AutoUpdate GREEN

- Evidence: reports/p4_hello_ai_1_0_4_postmortem.md

- 2025-09-11T23:50:16Z: P4-NW READY — dev access via 8080 confirmed (make hello-health)

## Phase 4: Observability & Secrets ✅
**Completed**: 2025-09-13

### Achievements
- **Metrics**: /metrics → Prometheus (targets up==1) → Grafana "Hello AI / SLO" dashboard
- **Alerts**: PrometheusRule with 3 SLO-based alerts (Down/Latency/ErrorRate)
- **Secrets**: ESO + SOPS platform deployed, AlertmanagerConfig wired
- **Evidence**: Comprehensive reports in `reports/p4_*`

### Production Status
- ServiceMonitor: ✅ Auto-detected and configured
- Prometheus scraping: ✅ Active and healthy
- Grafana dashboard: ✅ Visualizing metrics
- Alert rules: ✅ Loaded and evaluated
- ESO: ✅ 3/3 pods running
- SecretStore: ✅ Ready with RBAC
- ExternalSecret: ✅ Synced

### Key Deliverables
- Scripts: `p4_metrics_auto_setup.sh`, `p4_b_alerts_oneshot.sh`, `p4_c_secrets_oneshot.sh`
- PRs: #235 (metrics + alerts), #236 (secrets platform)
- Tag: p4-complete-20250913

## Phase 5: Scaling & Migration (Current)
**Status**: In Progress (2025-09-13 ~ )

### Objectives
- **P5-1**: Knative Autoscaling (HPA/KPA) with scale-to-zero ✅
- **P5-2**: SLO formalization and runbook creation ✅
- **P5-3**: First Compose service migration to Knative ✅
- **P5-4**: Secrets platform production hardening

### Success Criteria
- [x] Autoscaling demonstrated under load (evidence captured)
- [x] SLO targets defined and measured
- [x] At least one service successfully migrated (watcher + 4 bulk services)
- [ ] Cloud secret backend integrated

### Completed P5 Milestones
- **P5-1 Autoscale**: Scale-to-zero achieved, 14,272 RPS sustained (reports/p5_1_autoscale_20250913_055540.md)
- **P5-2 SLO**: 99.9% availability, P95<500ms latency targets defined (reports/p5_2_slo_20250913_060915.md)
- **P5-3 Migration**: 5 services migrated with full observability (watcher, curator, planner, synthesizer, archivist)

## Trial Mode (実験的運用)
**Status**: Active
**Started**: 2025-09-15

### Scope
- **Purpose**: 高速実験・検証サイクルを回すための一時的な運用モード
- **Duration**: 必要に応じて有効化/無効化（通常は1-2週間単位）
- **Authority**: STATE/current_state.md が最優先の真実源

### Template (Trial Mode時の構造)
```yaml
trial_mode:
  active: true
  focus: "特定の実験目標"
  experiments:
    - name: "実験名"
      status: "planning|running|completed|failed"
      evidence: "reports/trial_*.md"
  constraints:
    - "main branch の安定性維持"
    - "既存CI/CDパイプラインへの影響最小化"
```

### WIP (Work In Progress)
- [ ] Trial Mode テンプレート定義
- [ ] 実験ブランチ命名規則: `trial/*`
- [ ] Evidence: `reports/trial_*.md` 形式で記録

### Operating Rules
1. **Fast Iteration**: 完璧さより速度優先（後で本実装）
2. **Evidence First**: 全実験に証跡必須
3. **Rollback Ready**: いつでも main に戻せる状態維持
4. **Time-boxed**: 各実験は最大2週間

---
*Last Updated: 2025-09-15 00:00:00 UTC*
