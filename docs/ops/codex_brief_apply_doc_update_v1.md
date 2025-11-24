# Codex Brief: Apply doc_update_proposal_v1 v1
repo=vpm-mini / branch=main  
Phase 2 (PM Kai v1 + Layer B / Proposer & Reviewer Kai → Codex 連携フェーズ)

このドキュメントは、Codex に対して doc_update_proposal_v1 を適用させるときの標準ブリーフ v1 を定義する。

目的:

- Human（啓＋ChatGPT）が「この proposal は採用してよい」と判断したあと、
  毎回同じ“型”で Codex に依頼できるようにすること。
- Codex 側は proposal JSON をそのまま読み、updates[] を機械的に適用して PR を作るだけにすること。

このドキュメント自体は「運用マニュアル」であり、実際の実装（Python スクリプト等）は別の PR で行う。

---

## 1. 前提

- リポジトリ: HirakuArai/vpm-mini
- 作業ディレクトリ: ~/work/vpm-mini
- doc_update_proposal_v1 JSON が存在していること:
  - 例: reports/doc_update_proposals/2025-11-24_vpm-mini.json
- Human（啓）がすでに proposal＋review を読んでおり、
  「この proposal は apply してよい」と判断済みであること。

---

## 2. Codex に伝えたい責務

Codex にお願いしたいのは、次の 4 点だけである。

1. main を最新化し、作業ブランチを切る。
2. 指定された proposal JSON を読み込み、updates[] を順に適用する。
3. 変更をコミットして push する。
4. PR を作成し、proposal のパスと主な変更点を本文に含める。

重要:

- Codex は proposal の内容を解釈し直さない。
- target.path / change_type / suggestion_markdown に従って、
  できるだけ機械的に編集する“実行器”として振る舞う。

---

## 3. ブリーフ v1 のひな形（Human が書く部分）

Human が Codex に渡すブリーフ v1 の例（イメージ）は以下のとおり。

- リポジトリを ~/work/vpm-mini にして main を最新化すること。
- PROPOSAL_PATH に対象の proposal JSON（例: reports/doc_update_proposals/2025-11-24_vpm-mini.json）をセットすること。
- PROPOSAL_PATH の存在を確認すること。
- ブランチ名を "apply/＜proposalファイル名ベース＞" で作成・切り替えすること。
- PROPOSAL_PATH を読み込み、updates[] を target.path / change_type / suggestion_markdown に従って適用し、変更を保存すること。
- 変更後に git status / git diff を確認し、内容をコミットして push すること。
- PR タイトルは "Apply doc_update_proposal: ＜proposal ファイル名＞" とし、
  本文には PROPOSAL_PATH と主な変更点の概要を含めること。

実際のブリーフ文字列は、その時点の PROPOSAL_PATH に合わせて書き起こす。

---

## 4. apply スクリプトのインターフェース（設計メモ）

将来的に Codex に実装してもらう想定のヘルパー:

- パス: tools/apply_doc_update_proposal.py
- 想定インターフェース:
  - python tools/apply_doc_update_proposal.py PATH/TO/PROPOSAL.json

振る舞い（v1）:

1. JSON を読み込む。
2. updates[] を順に処理する。
   - target.path でファイルを開く（UTF-8 前提）。
   - change_type / suggestion_markdown に応じてテキスト編集する。
   - 編集結果を同じパスに上書き保存する。
3. エラー時は非ゼロ終了コードを返す。

このインターフェース仕様は、別 PR で実装する。

---

## 5. 運用ルール（v1）

- 必ず Human が proposal＋review を読んでからブリーフを書く。
- proposal JSON の中身は、apply 前後で変更しない。
- 適用後の PR は、通常通り Human がレビューしてからマージする。
- Codex は:
  - proposal の中身を再解釈しない。
  - 指定された PROPOSAL_PATH 以外のファイルを勝手に編集しない（バグがあれば後続 PR で修正する）。
