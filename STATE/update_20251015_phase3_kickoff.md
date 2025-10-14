# === Session Handoff (Single Source of Truth) ===
context_header: "repo=vpm-mini / branch=main / phase=Phase 3 Kickoff"

## 1) 現在地（C）
- ✅ Phase 2 完了（タグ: p2-4-green-20251015）
- 稼働KService: hello / metrics-echo（READY=True）
- 観測: Prometheus OK（hello up=1）。metrics-echo RPS は **恒久化対応中**

## 2) ゴール（G：Phase 3 Kickoff）
- P3-1: metrics-echo の RPS 可視化を恒久化（PodMonitor→Grafana→Evidence）
- P3-2: Grafana 自動スクショ（renderer + /render を Actions から）
- P3-3(任意): GHCR read:packages 設定のEvidence化
- P3-4(任意): “Empty reply” 切り分けメモ化

## 3) δ（次の一手）
- A) PodMonitor追加→Prometheus scrape確認→Grafana RPS更新→Evidence → 小PR
- B) Grafana 画像自動生成（renderer有効化＋Actions /render）→ 雛形PR

## 4) 進捗ログ（Phase 3）
- PR #380 (**p3-1**): PodMonitor + Grafana RPS + Evidence（**スクショ追加済みに更新予定**）
- PR #381 (**p3-2**): renderワークフロー雛形（placeholder）作成済み

## 5) 運用ルール
- 推測禁止：観測→判断→一手。**同じ手の反復禁止**
- PRは小さく（A/B分離）、各PRに DoD / Evidence / SSOT を同梱
