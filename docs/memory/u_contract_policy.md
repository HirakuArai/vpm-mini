
u_contract_policy v1（M2: ルール運用 → 半自動）
1. 目的

u_contract 系 PR（「理解の契約」のサンプルやレポート永続化など）が増えた際に、

どの PR を 自動マージしてよいか

どの PR は 人間がレビューすべきか

どの PR は クローズ / アーカイブしてよいか

を、一貫したルールで判断できるようにする。

本ポリシーは M2（ルール運用 → 半自動）フェーズを前提とし、

/ask pr_groomer_suggest

/ask update_north_star

Codex（devbox）

と組み合わせて運用されることを想定している。

2. 適用スコープ

対象リポジトリ: HirakuArai/vpm-mini

対象 PR:

タイトル・ラベル・パスなどから 「u_contract 系」と判定できる PR

例:

タイトルに u_contract を含む

ラベルに u_contract / u-contract などが付与されている

変更ファイルに docs/contract/ / docs/memory/*u_contract* などを含む

対象モード:

/ask の ASK_MODE が u_contract 系のとき

/ask pr_groomer_suggest のコンテキストに含まれる PR のうち、u_contract 系と判定されたもの

3. カテゴリ定義（v1）

u_contract 系 PR を、まずは次の 3〜4 カテゴリに分類する。

3-1. persist-report（レポート永続化）

意味:

bot / Codex が生成したレポート（例: Evidence, cost sweep, run summary など）を
reports/** 以下に永続化するだけの PR。

典型的なシグナル:

変更ファイルが reports/ 以下に限定されている。

コード・設定ファイル・STATE は変更しない。

PR 本文に「auto-generated」「persist report」などの文言がある。

デフォルトアクション（v1）:

🔄 CI Green なら auto-merge してよい候補。

前提条件:

CI Green（lint / tests / guards がすべて通っている）。

reports/ 以外に変更がないことを確認。

/ask 連携の想定:

/ask pr_groomer_suggest が kind: persist-report などと判定した場合、
このカテゴリにマップする。

将来的には auto-merge ラベル付与 → auto-merge 有効化まで自動化する余地あり。

3-2. sample-candidate（サンプル候補）

意味:

/ask 用の 代表サンプル / 教師データ候補 を追加・修正する PR。

典型的なシグナル:

docs/ や data/ 以下にサンプル JSON / Markdown / spec を追加している。

PR 本文で「サンプル」「例」「template」などの文言がある。

コードそのものよりも「ケース定義」「期待される入出力」の記述が中心。

デフォルトアクション（v1）:

👀 必ず人間がレビューする。auto-merge しない。

理由:

サンプルは LLM の振る舞いに直接影響するため、
意図と表現のズレを人間がチェックしたい。

/ask 連携の想定:

/ask pr_groomer_suggest が kind: sample-candidate と判定した場合、
このカテゴリにマップする。

レビュー完了後に sample-approved ラベルを付ける運用などを検討。

3-3. sample-archive（サンプル整理・アーカイブ）

意味:

古いサンプルを整理・統合・アーカイブする PR。

典型的なシグナル:

古いサンプルファイルの削除・移動が中心。

PR 本文で「archive」「cleanup」「obsolete」などの文言がある。

デフォルトアクション（v1）:

👀 軽めの人間レビューを行う（レビューは必要だが、優先度は中程度）。

LLM の参照範囲からサンプルが消える可能性があるため、
一応の確認を通す。

/ask 連携の想定:

/ask pr_groomer_suggest が kind: sample-archive と判定した場合、
このカテゴリにマップする。

3-4. stale-or-obsolete（陳腐化・無効化候補）

意味:

すでに別の PR で代替されている、あるいはコンテキスト的に不要となった
u_contract 系 PR。

典型的なシグナル:

長期間更新されていない（例: 3ヶ月以上 open）。

似た内容の PR がすでに merge 済み。

Issue 側で「方針変更」「別Issueに統合」などが宣言されている。

デフォルトアクション（v1）:

🧹 close / superseded としてクローズする候補。

クローズ時には、コメントで:

なぜクローズするか

代替 PR / Issue がある場合はそのリンク
を明記する。

/ask 連携の想定:

/ask pr_groomer_suggest が kind: stale / kind: superseded などと判定した場合、
このカテゴリにマップする。

4. 決定マトリクス（v1）

u_contract 系 PR の扱いを、カテゴリ別にまとめる。

category	典型シグナル	default action (v1)	/ask pr_groomer_suggest との対応
persist-report	reports/** のみ変更、bot 生成レポート	CI Green なら auto-merge してよい	kind: persist-report → auto-merge 候補
sample-candidate	サンプル / 教師データの追加・修正	必ず人間がレビュー（auto-merge しない）	kind: sample-candidate → review 必須
sample-archive	古いサンプルの削除・統合	軽めのレビュー後に merge / close	kind: sample-archive → review 中〜低
stale-or-obsolete	長期放置、代替 PR 済み、方針変更など	コメントを残して close / superseded	kind: stale / kind: superseded → close 候補
5. 運用フロー（M2 時点）

M2 フェーズでは、完全自動ではなく **「人間＋/ask＋Codex の半自動」**で運用する。

PR グルーミング

u_contract 系 PR をバッチで選び、/ask pr_groomer_suggest を実行。

返ってきた JSON の kind / priority から、上記カテゴリにマップする。

人間の判断（匙加減）

各 PR について、上記ポリシーと実際の内容を見比べて、

auto-merge する

review に回す

close する

のいずれかを決定する。

グレーゾーンが多い場合は、ポリシーの方を後で更新する。

Codex による実行

決定したアクションを Codex 実行に落とし込む（例: ラベル付与、merge、close コメントなど）。

メモリ / EG-Space へのフィードバック

大きな方針変更や例外ケースがあれば、

docs/memory/u_contract_policy.md の更新

docs/memory/egspace_m2_insights.md への追記

を行う。

6. 今後の拡張余地（v2 以降）

/ask pr_groomer_suggest の JSON スキーマ拡張

confidence / risk / needs_human_review フラグなどを追加。

auto-merge のガード強化

Self-Cost / Evidence Footers との連携。

フェーズ進行に応じたカテゴリの細分化

例: sample-candidate を「spec-based」と「log-based」に分ける など。
