# Decision: 本質未実証の是正（Phase 0/2 へリセット）
Date: 2025-09-02
Refs: #125（観測ライン拡張）, #128（Evidence Check）

## 背景
- 表層のCI/観測は進んでいたが、**AIを中心に据えた本質的処理**（5ロール一周・READYなKService）が未実証。

## 決定
- SSOT を「Phase 2 Kickoff直前」に正規化し、**P2-1 → P2-2 を最優先で達成**。
- `.ops/deploy_freeze.json` は READY 証跡が揃うまで **true 維持**。#125 はその後に再開。

## 具体アクション（証跡）
1) Phase 0 サニティ  
- `playground.py`：対話→要約→プラン→エコーの一周  
- `make test` Green（JSON 妥当・要約圧縮・ROUGE-L基準）→ ログ/検証を `reports/` に保存

2) Phase 2 Kickoff  
- `scripts/p2_bootstrap_kind_knative.sh`（冪等）  
- `infra/k8s/overlays/dev/hello-ksvc.yaml` 適用  
- 証跡：  
  - `kubectl get ksvc hello` → `READY=True`  
  - `curl -sS http://<local-ingress>` → `HTTP 200`  
  - 以上を `reports/ksvc_hello_proof_YYYYMMDD.md` に添付

## DoD
- [ ] `STATE/current_state.md` / 本ドキュメントが main に存在  
- [ ] Phase 0 サニティのテスト結果を `reports/` に保存  
- [ ] `hello-ksvc` の READY / 200 の証跡を `reports/` に保存  
- [ ] `.ops/README.freeze.md` に Freeze 方針と解除条件を明記