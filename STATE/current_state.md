# === State Declaration (Single Source of Truth) ===
active_repo: vpm-mini
active_branch: main
phase: Phase 2   # Phase 1 完了 → 小規模 Swarm Kickoffへ
context_header: "repo=vpm-mini / branch=main / phase=Phase 2"
short_goal: "Phase 2 Kickoff（kind + Knative 足場構築）"
exit_criteria:
  - "P2-1 GREEN: kind + Knative (v1.18) 足場構築スクリプトが動作"
  - "P2-2 GREEN: Hello KService デプロイ成功（kubectl get ksvc hello → READY=True / curl→HTTP 200）"
updated_at: 2025-09-02T09:00:00+09:00

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
- Status: **GREEN (pending PR merge)**
- Evidence: `reports/p2_2_hello_ai_20250903_075647.md`
- Decision Log:
  - hello-ai KService を hyper-swarm にデプロイ（httpbin as placeholder）
  - kourier ポートフォワード + Host ヘッダで疎通（200）
  - Knative Serving 正常動作確認
