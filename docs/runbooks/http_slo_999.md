# HTTP SLO 99.9% Runbook

## Deploy Freeze / Unfreeze
- **Freeze 有効化**  
  - `echo '{"freeze": true}' > .ops/deploy_freeze.json`  
  - PR 作成 → Auto-merge で **CD 停止**
- **Unfreeze（解除）**  
  - `echo '{"freeze": false}' > .ops/deploy_freeze.json`  
  - PR 作成 → Auto-merge で **CD 再開**

## Post-Promotion Guard 初動
- **Guard 失敗時の自動動作**: ロールバック → Freeze → GitHub Issue 自動起票  
- **当面の運用**  
  1) Issue を確認（関連ログ/証跡のリンクを参照）  
  2) 原因対処（設定/リソース/容量など）  
  3) `Unfreeze` PR を作成 → CI green → Auto-merge で CD を再開  
  4) 失敗再現テスト → Canary 昇格の再試行

