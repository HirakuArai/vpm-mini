# Codex Brief Protocol v0

context_header: repo=vpm-mini / branch=main / phase=Phase 3 / topic=codex-brief-protocol

## 1. 目的と位置づけ

本プロトコルは、Codex（ローカル / devbox / VM などの実行エンジン）に対して、
「何を・どこで・どう実行してほしいか」を渡すための **標準フォーマット** を定義する。

ポイント:

- 指示の置き場所は **GitHub（Issue 本文 / コメント / PR コメント）** とする。
- 指示は codex-brief フェンスで囲まれた **機械可読なブロック** として記述する。
- ChatGPT（Web UI）や LLMリレー v0 は、このフォーマットに従った「指示書」を生成する。
- Codex は、将来的に codex-brief を GitHub API 経由で取得し、順次実行する（Phase 3 では人力橋渡しから開始）。

本ドキュメントは v0 であり、実運用に応じて拡張・変更されることを前提とする。

---

## 2. 置き場所（Where）

codex-brief は、次のいずれかに配置する:

- GitHub Issue 本文
- GitHub Issue コメント
- PR コメント

基本ルール:

- 1 codex-brief = 1 実行ユニット（1つのまとまりとして Codex に渡す単位）
- 実行対象のコンテキスト（repo / branch / workdir）は brief 内に明示する。
- 「どの Codex に読んでほしいか」（executor）は brief 内の executor フィールドで指定する。

---

## 3. フォーマット（What）

### 3.1 全体構造のイメージ

GitHub 上では、次のようなブロックとして記述する（例）:

    executor: devbox-codex
    context_header: repo=vpm-mini / branch=main / phase=Phase 3 / track=P3-2 metrics-echo
    repo: HirakuArai/vpm-mini
    branch: main
    workdir: ~/work/vpm-mini

    steps:
      - name: snapshot READY status for metrics-echo
        shell: |
          set -e
          NS=$(kubectl get ksvc -A | awk '/metrics-echo/ {print $1; exit}')
          if [ -z "$NS" ]; then
            echo "metrics-echo ksvc not found"; exit 1;
          fi
          mkdir -p reports/metrics-echo
          kubectl -n "$NS" get ksvc metrics-echo -o yaml > /tmp/metrics-echo-ksvc.yaml
          # TODO: YAML → Markdown レポートに変換するスクリプト呼び出しなど

    outputs:
      - type: pr
        title: "Reports: add metrics-echo READY snapshot for P3-2"
        commit_message: "reports: add metrics-echo READY snapshot for P3-2"
        files:
          - reports/metrics-echo/metrics_echo_ready_status_p3-2.md
        link_issue: 774

v0 の段階では、厳密な YAML/JSON スキーマよりも、

- 「人間が読める」
- 「Codex がテキストとして処理しやすい」

ことを優先する。より厳密なスキーマ化は codex_runner_design.md 側で検討する。

### 3.2 必須フィールド（v0）

- executor  
  - 実行すべき Codex レーンを示す文字列。
  - 例: devbox-codex, vm-codex, local-mac-codex など。

- repo  
  - GitHub リポジトリ名（owner/name 形式）。例: HirakuArai/vpm-mini

- branch  
  - 操作の前提とするブランチ名。例: main, chore/...

- workdir  
  - Codex 実行時の作業ディレクトリ。例: ~/work/vpm-mini

- steps  
  - 実行手順の配列。
  - 各要素は少なくとも:
    - name: 手順の説明（ログに出す用）
    - shell: シェルスクリプト（bash想定）の本文

- outputs  
  - 期待する成果物の配列。
  - v0 では主に type: pr（PR作成）を想定:
    - title: PRタイトル
    - commit_message: コミットメッセージ
    - files: 変更を期待するファイルパス配列
    - link_issue: 関連する Issue 番号（任意）

### 3.3 任意フィールド

- context_header  
  - 人間と LLM 用の文脈文字列。STATE や docs の context_header と揃える。

- notes  
  - 人間向け補足メモ。Codex が特別扱いしなくてもよい情報。

---

## 4. 使い方（Who & How）

### 4.1 ChatGPT / Planner 側の使い方

- ChatGPT（Web UI）や将来の Planner セルは、
  - 「やりたいこと」「対象ファイル」「期待する PR など」を言語化したうえで、
  - 上記フォーマットに沿った codex-brief を Issue / コメントに書き込む。

- 啓は、Phase 3 初期では:
  - ChatGPT が提案した codex-brief をレビューし、Issue (#774 等) に貼る。
  - 必要に応じて軽く修正する。

### 4.2 Codex 側の使い方（v0）

- Phase 3 の初期段階では、Codex の実行はまだ **人力トリガー** とする:

  1. 啓が devbox / ローカルで Codex を起動。
  2. 対象 Issue の codex-brief をコピペで渡す。
  3. Codex は brief の内容に従い、手順を実行 → PR 作成 → Issue に結果コメントを返す。

- 将来的には codex_runner_design.md に基づき、
  - Codex / VM が GitHub API から codex-brief を取得し、
  - 未処理 brief を自動で発火する仕組みを導入する。

---

## 5. LLMリレー v0 との関係

- LLMリレー v0（/ask ワークフロー）は、
  - これまで通り Issue / PR コメントから /ask ... を拾い、
  - JSON patch や plan を返す役割を担う。

- 将来的には、/ask の出力をもとに:
  - LLMリレーが codex-brief を生成して Issue に追記
  - Codex が codex-brief を読んで実行
  という流れを想定している。

本プロトコルは、その「橋渡しフォーマット」として機能する。

---

## 6. 今後の拡張ポイント（v1 以降）

- steps の型拡張:
  - シェル以外（python / make / kubectl専用ステップ など）のサブタイプ定義。

- outputs の型拡張:
  - type: comment（Issue / PR コメントだけ残す）
  - type: report（reports/** に Markdown レポートを追加）

- エラー時の扱い:
  - status: success / failure / partial といった実行結果メタデータをどこに残すか。

これらは Phase 3 の運用状況と、codex_runner_design.md の議論に応じて拡張する。
