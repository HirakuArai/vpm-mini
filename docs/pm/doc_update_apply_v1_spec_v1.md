# doc_update_apply_v1 spec v1 (Tsugu / vpm-mini)

context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Layer B / doc_update apply v1)

このドキュメントは、Aya→Sho→Human レビュー済みの doc_update_review_v1.json を Tsugu workflow から機械的に適用するための v1 仕様を定義する。対象は STATE/ と docs/ 配下のテキストファイルに限定し、コードや Workflow には触れない。v1 は手動ボタン起動で PR 作成までを自動化し、マージは必ず人間レビュー前提とする。

## 1. レーン構造と Tsugu の責務
- Aya: 黒板や PM Snapshot を入力に doc_update_proposal_v1.json を生成。
- Sho: proposal をレビューし、doc_update_review_v1.json を生成（auto_accept_v1 / risk 判定）。
- Human（啓＋PM Kai）: proposal / review を目視確認し、方向性を承認。
- Tsugu: doc_update_review_v1.json をもとに STATE/docs を更新するブランチと PR を機械的に作る（apply 専用）。

## 2. 入力仕様（doc_update_apply_v1）
- project_id: 例 "vpm-mini"
- review_run_id または review_artifact_ref（例: Actions run id と artifact 名 doc_update_review_v1_*）
- apply_mode（オプション）: "docs_only"（v1 デフォルト）
- doc_update_review_v1.json の前提:
  - risk が "low"
  - review_mode が "auto_accept_v1"（または同等の safe モード）
  - target_files の path が STATE/ または docs/ 配下
- 前提を満たさない場合は apply を中止し、エラー扱い（PR を作らない）。

## 3. 出力仕様（Tsugu が行うこと）
- ファイル更新: review の target_files[].final_content を用いて対象ファイルを全置換（v1 は全体差し替えのみ）。
- Git 操作:
  - ブランチ名: 例 feature/doc-update-apply-2025-11-30 または feature/doc-update-apply-{review_run_id}
  - コミットメッセージ案: docs(state): apply doc_update_review_v1 {date or run_id}
  - PR タイトル案: Docs: apply doc_update_review_v1 to STATE/docs (vpm-mini)
- PR には doc_update_review_v1.json のリンクや対象ファイル一覧を本文に添付する想定。マージは人間が行う。

## 4. 安全ガード（v1 制約）
- 変更対象は STATE/ と docs/ のテキストのみ。src/ や .github/workflows/ などは変更しない。
- risk が "low" 以外や review_mode が auto_accept_v1 以外は apply しない。
- apply は workflow_dispatch の手動起動のみ（自動トリガーなし）。
- auto-merge は使わず、必ず人間レビューを経てマージする。問題があれば Tsugu PR を修正/クローズする。

## 5. 反映方法（apply 単位）
- review の target_files 単位: 各 path について final_content を 1 つ持つ前提（複数や欠落はエラー）。
- Tsugu v1 は「ファイル全体差し替え」を行い、セクション単位のマージは v2 以降に検討。doc_update 側で置き換え範囲を決めて final_content を作る前提。

## 6. 運用フロー（v1 想定）
- Aya: 黒板 entry に基づいて doc_update_proposal_v1.json を生成。
- Sho: doc_update_review_v1.json を生成（auto_accept_v1 / risk=low）。
- Human: proposal/review を確認し方向性を承認。
- Tsugu workflow（doc_update_apply_v1）を手動起動（project_id と review_run_id/artifact_ref を指定）。
- Tsugu: STATE/docs を更新したブランチと PR を作成。
- Human: PR をレビューしてマージ。

## 7. 将来拡張メモ（v2 以降）
- セクション単位マージ（部分差し替え）の仕様化。
- 複数 review をまとめて apply するバッチモード。
- reports/ など特定ディレクトリの追随自動化モード。
- 黒板やラベルをトリガーにした自動起動の導入は、v1 運用実績を踏まえて検討。
