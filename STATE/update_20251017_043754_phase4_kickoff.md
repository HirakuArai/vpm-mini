# === Phase 4 Kickoff ===
context_header: "repo=vpm-mini / branch=main / phase=Phase 4 Kickoff"

## 現在地（C）
- Phase 3 完了（自動Evidenceライン/自動マージ/週次掃除が安定稼働）
- 直近Evidence: reports/p3_2_grafana_auto_render_*.md / img/grafana_p3_2_auto_*.png

## 短期ゴール（G）
- **P4-1**: Knative移植の縦スライス #1（対象サービス：candidate-a）
  - 最小DoD:
    - [ ] KService マニフェスト（env/secret/configの最小移植）
    - [ ] デプロイ後 READY=True
    - [ ] /metrics または主要エンドポイントの UP=1 を確認
    - [ ] Evidence（MD+PNG）と SSOT 反映、PRはAuto-merge

- **P4-2**: 外形監視(blackbox/uptime)の導入 → SLO基礎の可視化

## δ（次の一手）
- A) P4-1 の対象 candidate-a を `infra/k8s/overlays/dev/` に雛形追加 → 動作/Evidence → 小PR
- B) P3 自動Evidenceラインを踏襲し、P4-1 のダッシュボード枠を予約

## 参照
- タグ: p3-green-20251017
- Workflows: render_grafana_png / auto_merge_evidence / weekly_artifact_cleanup
