## Phase 2-2: Hello KService READY=True
- Evidence: reports/phase2/hello_ready.md（apply → wait → get, READY=True）
- Notes: /ask 経路と保存PRライン安定、executor dry-run 緑
- Next: Autoscale PoC → 既存サービスのKnative移植 → 監視ラインのK8s側移設

### Phase 2 / Runner + /ask パイプの状態（2025-11-14 時点）
- **T2:** `/ask` → Evidence PR → `codex/inbox/ask_<ts>.json` → Runner(DRY) → `_done/` と `run.log` までの一巡を PR #660 で実証済み。
- **T3:** `RUN_MODE=exec` で非破壊な `kubectl get ...` Canary を実行し、`reports/codex_runs/**` に `[EXEC] kubectl ...` が残ることを確認（PR #694）。
- **S5:** `/ask` コメントに `S5 apply: dev hello-ksvc` がある場合、Producer が apply JSON を生成し、Runner(exec) が `infra/k8s/overlays/dev/**` に対して `kubectl diff/apply/get` を実行して `apply.log` / `after.yaml` / `run.log` を残すパスまで通った（PR #696, #702）。
- **現状の制約:** Runner の起動は Codex (VM) からの手動 `RUN_MODE=dry/exec` に限定。実クラスタでは Knative CRD と hello リソースが未整備のため、`hello-ksvc` の apply はエラーになる（CRD 整備 or 対象リソースの見直しが必要）。

### Phase 2 / Goal-M2: S5 apply + hello-ksvc 一巡

- dev hello-ksvc 環境:
  - devbox-codex 上の kind クラスタ `vpm-mini`（kube-context: `kind-vpm-mini`）
  - このクラスタ上に Knative Serving v1.18 + kourier を導入し、
    `infra/k8s/overlays/dev/hello-ksvc.yaml` を apply して READY=True を確認する。
  - hello / metrics-echo の両 KService が READY=True で応答し、S5 apply の標準ターゲットとして扱える状態。
- この環境を、Runner + /ask / S5 apply の「標準的な dev 実行先」として扱う。
- 後続タスク:
  - `infra/kind-dev/kind-cluster.yaml` の定義
  - `scripts/p2_bootstrap_kind_knative.sh` による kind+Knative 足場構築
  - S5 apply 経由で hello-ksvc を更新 → READY=True を Evidence 付きで確認

Note: STATE に環境の最新状況を十分反映できていなかったため、危うく dev クラスタ削除判断に傾きかけたことを忘れずにおく。

### PR と SSOT の扱いルール

- まず、「この PR の変更内容は SSOT（main に残すべき情報）かどうか」で判断する。
  - コード／インフラ（scripts/**, infra/**, .github/**）
  - ドキュメント／STATE／定義（STATE/**, docs/**, data/**）
  - 将来も参照したい公式な Evidence（reports/** や codex/inbox/** のうち意味のあるもの）
    は SSOT として main に残す。
  - 一時的な実験や ad-hoc なログなど、今後の判断に使わないものは非SSOTとして扱い、役目が終わったら Close でよい。

- SSOT な PR（本流）は、必ず「merge」または「Close＋理由コメント」で決着させる。
  - 「Open PR = まだ決着していない議題のリスト」という前提を維持する。

- 実験／デバッグ PR は、結果が本流PRや STATE／ドキュメントに反映された時点で Close するのが基本で、merge されないのが通常。
  - 学びがあれば SSOT 側（STATE や docs、定義ファイルなど）に昇格させる。

- 異常／要調査 PR は、その場で「捨てる（非SSOTとして Close）／修正して反映（SSOTとして別PRへ）／保留」の扱いを決める。
  - 保留にする場合は、必ず「なぜ保留か」を PR コメントなどに明記して Open のまま残す。
