# Mini Loop v0 job format

目的:

- Mini Loop v0 で、`jobs/queue/*.json` に置かれた job をどう表現するかを定義する。
- devbox / runner 側が job を解釈できるように、最小限のフィールドセットを決める。

v0 で使うフィールド:

- `id` (string): job の一意な ID（ファイル名と同じでもよい）
- `kind` (string): v0 では `"run_shell"` のみを想定
- `workdir` (string): コマンドを実行する作業ディレクトリ（例: `/workspace/vpm-mini`）
- `script` (array[string]): 順番に実行するシェルコマンドの配列
- `dod` (string): DoD（成功条件）の記述。v0 では `"exit_code == 0"` を前提とするが、フィールドとして残す
- `report_path` (string): stdout / stderr / exit code などの結果を書き出す先（例: `reports/jobs/2025-11-XX-001.out`）

JSON 例:

```json
{
  "id": "2025-11-XX-001",
  "kind": "run_shell",
  "workdir": "/workspace/vpm-mini",
  "script": [
    "git status -sb"
  ],
  "dod": "exit_code == 0",
  "report_path": "reports/jobs/2025-11-XX-001.out"
}
```

備考・将来拡張:

- まだ `"run_shell"` の単一種類のみを扱う。`update_docs` や `kubectl_apply` など別種類の job は後続バージョンで検討する。
- DoD も v0 では exit code 判定のみ。将来、ファイル存在や文字列マッチなど複雑な DoD を拡張できるよう、`dod` フィールドは残しておく。
- runner は `report_path` を前提に結果を残す。必要に応じて GitHub コメントなど別の出力先を追加する拡張を想定する。
