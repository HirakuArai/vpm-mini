# deploy_freeze 運用ノート
- 目的：本番系CDの暴発を防ぎ、**READYな計測対象が揃うまで**観測ライン拡張(#125)を停止する。
- 現状：`.ops/deploy_freeze.json` = `true`（解除条件は下記）

## 解除条件
1. Phase 0 サニティ完了（5ロール一周・`make test` Green・証跡保存）
2. Phase 2 Kickoff完了（`hello-ksvc` READY=True / `curl` HTTP 200・証跡保存）

※ 上記**両方**を `reports/` の証跡で確認後、freeze を解除して #125 を再開する。