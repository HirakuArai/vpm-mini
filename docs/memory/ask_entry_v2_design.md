
ask-entry v2 設計メモ（M-phase）
1. 現状（v1）の整理
1.1 役割

.github/workflows/ask-entry.yml は、GitHub Issue / PR コメントでの /ask ... を受け取り、

OpenAI への問い合わせ

レスポンスの整形

必要に応じて u_contract や Evidence を PR にぶら下げる
を行う ChatOps エントリポイント。

1.2 v1 の前提

/ask の主用途は「u_contract を生成して永続化する」ことだったため、ワークフローはほぼ以下を前提に組まれている。

コメント本文から prompt を構築する（Build prompt）

OpenAI に投げる

レスポンスから u_contract.json を out/ に書き出す

out/u_contract.json を reports/ask/ask_*.json として PR ブランチに保存

ask: persist u_contract (...) という PR を自動で作る

この結果、次のような前提に依存している。

「すべての /ask は、最終的に u_contract.json を生成する」

「Save-PR ステップでは out/u_contract.json が必ず存在する」

1.3 問題点（M-phase 観点）

M-phase で新しく導入した以下の /ask と相性が悪い。

/ask update_north_star

STATE / vpm_memory_min.json の差分案(JSON)をコメントとして返したい。

必ずしも u_contract をファイルとして残す必要はない。

/ask pr_groomer_suggest

Open PR 群の分類結果(JSON)をコメントとして返したい。

こちらも u_contract は必須ではない。

実際に /ask update_north_star を投げたところ：

Build prompt ステップでシェルの syntax error（u_contract 用の前処理が前提を満たさず終了）

Save-PR ステップで out/u_contract.json が無くて cp エラー

OpenAI 呼び出しまで到達しない

結果として、「M-phase 用の /ask をそのまま使うと ask-entry 側で落ちる」という段差がある。

2. v2 の方針（複数モード対応）
2.1 基本方針

/ask を モードごとに扱う。

例: mode = "u_contract" | "update_north_star" | "pr_groomer_suggest" | ...

モードに応じて：

プロンプトのテンプレート

OpenAI への I/O フォーマット

Save-PR 等の後処理
を切り替える。

v1 での前提「すべての /ask が out/u_contract.json を生成する」を外し、
「一部のモードだけが u_contract を生成し、他はコメント返信のみ／軽量 Evidence のみ」 にする。

2.2 モードの決定方法（案）

シンプルさ優先で、まずはコメント本文の 1 行目 or 2 行目を見て決める。

/ask update_north_star → mode = update_north_star

/ask pr_groomer_suggest → mode = pr_groomer_suggest

/ask 単体、または /ask persist_u_contract 的な既存形 → mode = u_contract

将来的には、CONTEXT_JSON の中に mode フィールドを持たせる余地も残しておく。

2.3 モードごとの挙動（v2ドラフト）
(A) mode = u_contract（現行の主用途）

目的：u_contract を生成し、reports/ask/ask_*.json に永続化する。

挙動：

コメント本文から u_contract 用プロンプトを組み立てる。

OpenAI から u_contract JSON を受け取る。

out/u_contract.json として保存。

Save-PR ステップで reports/ask/ask_*.json にコピー。

ask: persist u_contract (...) PR を作成（または既存 PR に追加）。

v1 からの差分：

現在のフローをほぼそのまま残すが、「他モードとは分岐する」前提で書き直す。

(B) mode = update_north_star

目的：STATE/current_state.md と data/vpm_memory_min.json に対する差分案を JSON でコメント返信する。

挙動（高レベル）：

コメント本文の CONTEXT_JSON をそのまま OpenAI に渡す。

update_north_star_spec で定義したフォーマット（state_patch / memory_patch / rationale / warnings）でレスポンスを受け取る。

PR やブランチは作成せず、Issue/PR コメントとして JSON を返信する。

必要であれば、軽量なログ（例: reports/ask_runs/**）を追加するが、u_contract.json は作らない。

Save-PR ステップの扱い：

mode=update_north_star の場合は 完全にスキップ。

out/u_contract.json の存在を前提にしない。

(C) mode = pr_groomer_suggest

目的：Open PR 群の分類（ssot / ephemeral / needs-triage / blocked）と推奨アクションを JSON でコメント返信する。

挙動は update_north_star に類似：

コメント本文の CONTEXT_JSON を OpenAI に渡す。

pr_groomer_spec のフォーマット（classifications / rationale / warnings）でレスポンスを受け取る。

コメントとして返信。u_contract や Save-PR は行わない。

(D) その他のモード

将来、「Metrics まわりの /ask」などが出てきた場合に追加モードを検討する。

v2 ドラフトでは (A)〜(C) を優先対象とする。

3. ワークフロー構造の変更イメージ
3.1 現状の問題箇所

Build prompt ステップのシェルスクリプト内（例: .github/scripts/ask_build_prompt.sh 等）で、

コメント解析 → u_contract 専用 prompt 構築 → out/u_contract.json 前提の後処理
が1本にまとまっている。

Save-PR ステップで cp out/u_contract.json ... を無条件に実行している。

3.2 v2 での構造案

おおまかには以下のような分岐を導入する。

Step: Detect mode

コメント本文を解析し、ASK_MODE 環境変数を決定。

Step: Build prompt (mode-specific)

ASK_MODE に応じてプロンプトを組み立てる。

Step: Call OpenAI

共通ステップだが、ASK_MODE に応じて違う system / user プロンプトを選択可能にしておく。

Step: Normalize & Coerce

mode ごとに期待する JSON スキーマを適用。

Step: Persist artifacts (optional, mode-specific)

ASK_MODE = u_contract のときだけ u_contract.json を保存し、PR を作成。

ASK_MODE = update_north_star / pr_groomer_suggest のときはコメント返信のみ。

v2 ドラフト時点では、YAML 変更の細部は別タスクとし、このドキュメントでは「構造」と「責務の分かれ目」を明確にする。

4. M-phase における導入ステップ案

Step-1: ドキュメント整備（本ファイル）

v2 のモード構造と挙動を合意形成用にまとめる。

Step-2: mode detection + Save-PR 分岐の最小変更

ASK_MODE を導入し、u_contract 以外のモードでは Save-PR ステップをスキップする。

まずは /ask update_north_star が落ちなくなることを目標にする。

Step-3: update_north_star / pr_groomer_suggest 専用プロンプトの組み込み

それぞれ docs/memory/*_spec.md を参照しながら、ワークフロー内のプロンプトテンプレートを整備。

Step-4: u_contract persist 周りの整理

Task-M2 (#738) のポリシーに従って、古い u_contract PR の掃除やローテーションを進める。

必要に応じて ask-entry に「一定期間を過ぎた u_contract を自動アーカイブする」ロジックを追加。

5. このドキュメントの役割

M-phase における ask-entry の「変更設計図」として使う。

実際の YAML / スクリプト変更は別 PR で行い、その PR から本ファイルへのリンクを張る。

将来的に v2 実装が完了したら、ここに実装状況やモード一覧をアップデートする。
