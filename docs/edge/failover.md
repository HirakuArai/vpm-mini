# Edge Failover（HAProxy / dev 実演）

**目的**: dev 環境で Edge L7（HAProxy）により **cluster-a → cluster-b** の自動切替（active/backup）を検証する。

## 1. エンドポイント
- **Edge**: `http://localhost:30080/hello`（統一入口）
- **Backend**:
  - cluster-a: `http://localhost:31380/hello`（primary）
  - cluster-b: `http://localhost:32380/hello`（backup）
- **ダッシュボード**: `http://localhost:30090/stats`

## 2. 起動
```bash
bash scripts/phase5_failover_bootstrap.sh
# HAProxy (:30080 / :30090) が立ち上がり、/hello 200 を返すことを確認
```

## 3. フェイルオーバー演習
```bash
bash scripts/phase5_failover_verify.sh
# 手順: aのingress停止 → 連続200検出 → RTO測定 → 品質(成功率/latency)測定 → a回復
# 判定: RTO ≤ 60s / success ≥ 95% / p50 < 1000ms
# 結果: reports/phase5_failover_result.json / スナップショット md
```

## 4. 本番置換（参考）
- HAProxy on localhost は **実演用**。本番は **GSLB/DNS/Edge LB** に置換
- 監視は **L7 ヘルスチェック**（2xx）＋リージョン/ゾーン重み付け
- 切替フローは **RTO/RPO 要件**に合わせて閾値/ヒステリシスを調整

## 5. トラブルシュート
- **/hello が 200 にならない**: NodePort 設定（31380/32380）と HTTPRoute を確認
- **スクリプト失敗時**: `A_CTX/A_NS/A_DEP` の環境変数を明示

## 6. 検証基準
- **RTO**: ≤ 60 秒（フェイルオーバー時間）
- **成功率**: ≥ 95%（継続サービス提供）
- **レイテンシ**: P50 < 1000ms（性能維持）
