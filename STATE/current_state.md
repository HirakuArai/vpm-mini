## Phase 2-2: Hello KService READY=True
- Evidence: reports/phase2/hello_ready.md（apply → wait → get, READY=True）
- Notes: /ask 経路と保存PRライン安定、executor dry-run 緑
- Next: Autoscale PoC → 既存サービスのKnative移植 → 監視ラインのK8s側移設

### Phase 2 / Runner + /ask パイプの状態（2025-11-14 時点）
- **T2:** `/ask` → Evidence PR → `codex/inbox/ask_<ts>.json` → Runner(DRY) → `_done/` と `run.log` までの一巡を PR #660 で実証済み。
- **T3:** `RUN_MODE=exec` で非破壊な `kubectl get ...` Canary を実行し、`reports/codex_runs/**` に `[EXEC] kubectl ...` が残ることを確認（PR #694）。
- **S5:** `/ask` コメントに `S5 apply: dev hello-ksvc` がある場合、Producer が apply JSON を生成し、Runner(exec) が `infra/k8s/overlays/dev/**` に対して `kubectl diff/apply/get` を実行して `apply.log` / `after.yaml` / `run.log` を残すパスまで通った（PR #696, #702）。
- **現状の制約:** Runner の起動は Codex (VM) からの手動 `RUN_MODE=dry/exec` に限定。実クラスタでは Knative CRD と hello リソースが未整備のため、`hello-ksvc` の apply はエラーになる（CRD 整備 or 対象リソースの見直しが必要）。
