# === State Declaration (Single Source of Truth) ===

**active_repo**: vpm-mini  
**active_branch**: main  
**phase**: Phase 2  # Phase 1 完了 → 次フェーズへ  
**context_header**: "repo=vpm-mini / branch=main / phase=Phase 2"  
**short_goal**: "Phase 2 Kickoff (kind + Knative) の足場構築"  

## プロジェクトの最終目的
Hyper-Swarm / VPM を構築し、常時自己進化型の開発運用基盤を確立する。

## 現在地（C）
- Phase 1 全タスク (S1–S10) 完了
- main ブランチには Docker Compose + Prometheus + Grafana が統合済み
- SSOT Snapshot: `phase1-complete` タグあり

## ゴール（G）
- Phase 2 Kickoff: kind + Knative 足場構築
- 小規模 Swarm (30→150セル) の PoC に備える

## 差分（δ）
- Docker Compose → Kubernetes への移行
- 観測ラインを K8s 環境に移植
