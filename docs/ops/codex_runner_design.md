# codex-runner Design v0

context_header: repo=vpm-mini / branch=main / phase=Phase 3 / topic=codex-runner-design

## 1. 目的とスコープ

codex-runner は、GitHub 上に置かれた codex-brief を読み取り、  
適切な Codex 実行環境（devbox / VM Codex など）で steps を実行し、  
結果を PR やコメントとして GitHub に書き戻す「実行オーケストレータ」として設計する。

本ドキュメントでは、以下を定義する。

- 対象とするコンポーネントと責務
- codex-brief のライフサイクル
- ポーリング／実行の基本フロー
- エラー処理・ログの方針
- Phase 3〜4 における段階的なロールアウトプラン

ここではあくまで v0 の設計とし、実装は Phase 3 後半〜Phase 4 で段階的に行う。

---

## 2. コンポーネントと責務

### 2.1 GitHub

- codex-brief の「唯一の保管場所」とする。
- 置き場所:
  - Issue 本文
  - Issue コメント
  - PR コメント
- codex-brief は、docs/ops/codex_brief_protocol.md で定義されたフォーマットに従う。
- 実行結果（PR、コメント、reports/**）も GitHub に集約する。

### 2.2 LLMリレー v0 (/ask ワークフロー)

- 既存の /ask ワークフローは、Issue/PR コメントから /ask ... を拾い、
  JSON patch や plan, warnings を返す役割を担う。
- codex-runner v0 の段階では:
  - /ask は「何を変えるべきか」「どんな作業が必要か」を提案する係。
  - codex-runner は「決まった作業を実際にやる」係。
- 将来的には、LLMリレーが /ask の結果をもとに codex-brief を自動生成する。

### 2.3 codex-runner

- 役割:
  - GitHub から codex-brief を取得し、
  - 実行対象を選別し、
  - steps.shell をシェル環境で実行し、
  - outputs に従った PR やコメントを作成する。
- バックエンドとして利用する実行環境:
  - Phase 3: devbox Codex を前提とした「半自動」実行
  - Phase 4: VM Codex (常設) を前提とした「自動」実行

### 2.4 Codex Executor（devbox / VM）

- codex-runner の指示に従い、実際にシェルコマンドを実行する役。
- git, gh, kubectl などの CLI を叩ける前提。
- ログ（実行したコマンド・結果）は codex-runner 経由で GitHub に残す。

---

## 3. codex-brief のライフサイクル

### 3.1 状態イメージ

codex-brief には、概ね次の状態があるとみなす。

- NEW: まだ誰も拾っていない codex-brief
- PICKED: codex-runner が処理対象として選択したもの
- RUNNING: 実行中（ジョブが走っている）
- DONE: 正常終了し、期待された outputs が GitHub に反映された
- FAILED: 実行中にエラーが発生し、中断した

状態管理の方法（v0案）:

- GitHub ラベル:
  - 例: `codex:new`, `codex:running`, `codex:done`, `codex:failed`
- または、Issue コメント内のチェックボックス:
  - [ ] codex: new
  - [x] codex: done

Phase 3 では、ラベル運用を優先し、履歴が追いやすい状態にする。

### 3.2 「処理済み」フラグ

- codex-runner は、同じ codex-brief を何度も実行しないようにする。
- NEW 状態の brief のみを拾い、RUNNING → DONE/FAILED に状態を更新する。
- エラー時 (FAILED) は、理由をコメントとして残し、人間が次のアクションを決められるようにする。

---

## 4. ポーリング／選択戦略

### 4.1 どこから拾うか

v0では、次のような単純な戦略を想定する。

- 対象リポジトリ: HirakuArai/vpm-mini
- 対象 Issue/PR:
  - ラベル `codex:enabled` が付いた Issue
  - あるいは特定の Project カラムに属する Issue (将来拡張)
- そこから:
  - 最新順でコメントをスキャンし、
  - NEW 状態の codex-brief ブロックを抽出する。

### 4.2 実行の頻度

- 手動トリガー:
  - Phase 3 前半では、人間が「codex-runner を一度走らせる」形で開始する（cronではなく手動）。
- 将来的な自動化:
  - Phase 3 後半〜4では、5〜15分間隔のポーリングを検討する。

---

## 5. 実行モデル（brief → 実行）

### 5.1 brief フィールドの使い方（v0）

codex_brief_protocol.md で定義したフィールドを、codex-runner は次のように解釈する。

- executor:
  - どの Codex 実行レーンで走らせるか。
  - 例: `devbox-codex`, `vm-codex`。
- repo, branch, workdir:
  - git clone 済み前提のローカルパスと、使用するブランチ。
- steps:
  - 配列の各要素に対し、`shell` フィールドをそのままシェルに流す。
  - v0 では、step 間の依存関係は単純に順次実行とする。
- outputs:
  - type: pr:
    - `files` に指定されたファイルが変更されていることを前提に、
      git add → commit → push → gh pr create を行う。
  - 将来: comment, report などの type を追加。

### 5.2 安全性と idempotency

- v0 では、次の安全策を優先する。
  - dry-run モードの検討（まず git diff や echo だけを行う brief）。
  - 同じ brief を複数回実行しても壊れないように、ブランチ名の命名規則を工夫。
  - 実行前後の git status / diff をログとして GitHub コメントに添付。

---

## 6. エラー処理とログ

### 6.1 エラー時のふるまい

- steps の途中でコマンドが失敗した場合:
  - その brief を `FAILED` とマークし、
  - エラー内容（標準出力 / 標準エラーのサマリ）を Issue コメントとして残す。
- ブランチが残った場合:
  - 人間が後続調査できるように、そのまま残す（自動削除しない）。

### 6.2 ログの残し方

- codex-runner 自身のログは、以下のいずれかで残す。
  - GitHub Issue コメント
  - 専用の reports/ops/** レポート
- 最低限、次の情報を記録する。
  - 実行した brief の ID（Issue番号＋コメントIDなど）
  - 実行日時
  - 使用した executor（devbox / VM）
  - 結果: success / failure
  - 生成した PR や報告レポートのリンク

---

## 7. ロールアウトプラン（Phase 3〜4）

### 7.1 Phase 3 前半: 手動 + 設計確立

- 状態:
  - codex-brief プロトコル (docs/ops/codex_brief_protocol.md) が v0 として存在。
  - /ask や ChatGPT から codex-brief を Issue に書くことができる状態。
- codex-runner:
  - まずは「人間が brief を見て、devbox で手動実行する」運用を続ける。
  - この設計メモをもとに、どの程度自動化したいか、どのレーンを優先するかを検討。

### 7.2 Phase 3 後半: devbox ベースの半自動ランナー

- devbox 上に codex-runner スクリプトを用意し、
  - `--dry-run` モードで brief → コマンド変換だけを試す。
  - 問題なければ `--execute` で実際に PR 生成まで行う。
- この段階では、まだ「人が明示的に codex-runner を起動する」。

### 7.3 Phase 4: VM Codex 常設 + 定期ポーリング

- VM Codex を常設させ、定期的に GitHub をポーリングする codex-runner を常駐させる。
- 実行対象:
  - ラベル `codex:auto` が付いた brief のみを自動処理する。
- 手動レーン:
  - 緊急対応や検証用に、devbox 上の手動 codex-runner も残す。

---

## 8. 今後の検討事項

- codex-brief の厳密なスキーマ定義（YAML/JSON Schema）
- brief の「優先度」や「期限」に応じたスケジューリング
- 実行権限の分離（読み取り専用レーン / 書き込み可能レーン）
- /ask ワークフローとのより密な連携（/ask → codex-brief 自動生成 → codex-runner 自動実行）
