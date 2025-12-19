# Domain Update Lane (Fact Lane) v1 — hakone-e2

目的：A(domain) SSOT を「evidence(URL) → API抽出 → Quality Gate → PR」で更新する最小レーンを作る。  
B(hakone-e2黒板)は触らない。

## Inputs（workflow_dispatch）
- url: evidence のURL（まずは HTML を想定）
- evidence_id: domain内でのID
- event_id: 紐づけ先イベント（任意）
- mode: dry-run | pr

## Output（run artifacts）
- reports/hakone-e2/runs/<run_id>/
  - extracted.json（モデル出力）
  - validated.json（スキーマ検証後）
  - conflicts.json（矛盾/重複検知）
  - domain.diff（domain差分）
  - patch_preview.md（要約）

dry-run でも run artifacts を GitHub Actions artifact としてアップロードする。

## Quality Gate（必須）
- claim は evidence_refs を必ず持つ
- refs の参照切れを出さない（entity/event/evidence）
- 同一 claim.key の value 不一致は conflict として検知し、PRは review-required とする（v1は一覧を出力）

## 運用ノート（M3で確定した運用知）

### mode=pr の PR作成は PR_BOT_TOKEN を使う（必須）
Fact Lane の `mode=pr` で作る PR は **PR_BOT_TOKEN（Fine-grained PAT）** を使って push / PR作成する。

理由：
- `GITHUB_TOKEN` を使って push / PR作成すると、そのイベントは（`workflow_dispatch` / `repository_dispatch` を除き）新しい workflow run を作成しない仕様がある。
  その結果、PRに required checks が設定されている場合に “Expected — Waiting for status to be reported” で止まり、マージ不能になることがある。

運用：
- GitHub Actions 側では、PR作成/Pushに `PR_BOT_TOKEN` を使用する（workflow内でoriginを書き換える等）。
- `PR_BOT_TOKEN` が未設定の場合は「PR作成までやらない（dry-runのみ）」に寄せるのが安全。

### workflow_dispatch の前提
- `workflow_dispatch` で UI（Run workflow）から手動実行したい場合、workflowファイルが **デフォルトブランチに存在する必要**がある。

### 命名の禁則（サニタイズ必須）
#### ブランチ名（Git ref 制約）
- ブランチ名は Git ref の命名制約に従う。入力（例: `evidence_id`）をそのままブランチ名に使うと、`:` などの禁則文字で失敗することがあるため、サニタイズして使う。

#### artifact名（upload-artifact 制約）
- `actions/upload-artifact` は `:` などの文字を artifact name に含むと失敗する（NTFS等を考慮した制約）。
  したがって artifact name は `run_id_safe`（禁則文字を `_` 等に置換したもの）を使用する。

### dry-run の確認観点（artifact）
- `validated.json`：schemaに合致しているか（facts patchとして成立しているか）
- `conflicts.json`：conflictsが 0 か（擬似矛盾が出ていないか）
- `domain.diff`：意図しない大量上書きが起きていないか
- `patch_preview.md`：run_id / url / conflicts の要約が妥当か

