# EG-Space M2 インサイトメモ（Hello S5 & PR Groomer）

## 1. 背景：M-phase の目的

M-phase（M-1〜M-2）では、以下を目的に「事象目的空間（EG-Space）」の実験を行った。

- CONTEXT_JSON という圧縮された Evidence 入力から、
  - North Star レイヤー（STATE + 最小メモリ）をどこまで更新できるか
  - どの解像度なら LLM の理解が破綻しないか
- `/ask` ベースの LLM リレーを通じて、
  - 人間の判断（匙加減）と Codex の更新を組み込んだ 1 サイクルを確立すること

## 2. Hello S5 / `/ask update_north_star` ループの学び

### 2.1 入力コンテキスト（CONTEXT_JSON）の最小構成

Hello S5 ラウンドでは、以下の情報だけを CONTEXT_JSON に載せた状態で `/ask update_north_star` を実行した。

- 直近の Evidence run:
  - run_id: `apply_hello_dev_20251115T183901Z`
  - reports_dir: `reports/codex_runs/apply_hello_dev_20251115T183901Z`
  - manifest: `infra/k8s/overlays/dev/hello-ksvc.yaml`
  - READY=True / timestamp
- 関連 PR の概要（spec/doc 追加）
- STATE / vpm_memory_min の拔粋
  - 「この run を正式な証跡として扱う」旨
  - `goal_m2.last_successful_s5_apply` など

この程度の情報量でも、LLM は次のようなパッチ案を返せることが分かった。

- STATE:
  - Hello S5 の Evidence 行（run_id / reports_dir / manifest / status / timestamp）の構造化追記案
- メモリ:
  - `goal_m2.last_successful_s5_apply` の `id` と `updated_at` を「実行 ID ＋ UTC 時刻」に揃える案
- warnings:
  - 既に STATE/メモリに同等情報があるため、差分は「厳密さの微調整レベル」であることの指摘

### 2.2 North Star 更新の「解像度（匙加減）」

Hello S5 ラウンドでは、以下の程度までを採用する方針とした。

- STATE:
  - `Goal-M2 / Hello S5 成功ルート Evidence` セクションに、Hello S5 run を 1 行で要約した Evidence 行を追加
  - 詳細説明は STATE ではなく reports/ や Issue に任せる
- メモリ (`data/vpm_memory_min.json`):
  - `goal_m2.last_successful_s5_apply.updated_at` だけを UTC に揃える
  - その他のフィールド（id/manifest/reports_dir/note/evidence_loop）は現状維持

この「中くらい寄りだけど控えめ」の解像度でも、EG-Space 上での C/G/δ の理解は破綻せず、

- 「Hello S5 の成功ルートはどの run を基準に整合したか」
- 「そのタイムスタンプは何か」

といった座標は十分に復元できることが確認できた。

## 3. PR Groomer / `/ask pr_groomer_suggest` ループの学び

### 3.1 入力コンテキスト（CONTEXT_JSON）の最小構成

u_contract 系 PR の一部（#731, #723）について、以下程度の情報で `/ask pr_groomer_suggest` を実行した。

- number / title
- labels（例: `ask`, `u_contract`, `sample-candidate`）
- head_ref / base_ref / author
- is_experiment_hint / notes_from_human

それでも LLM は、`docs/memory/pr_groomer_spec.md` に従い、次のように分類できた。

- #731:
  - カテゴリ: `persist-report/auto-merge`
  - 内容: u_contract の定型レポート永続化（reports/配下のみ、bot 生成、競合なし）
  - 推奨アクション: 自動マージ候補
- #723:
  - カテゴリ: `sample-candidate/needs-review`
  - 内容: ask-entry 経路の代表 u_contract サンプル
  - 推奨アクション: 自動マージはせず、人間レビューのうえでサンプルとして扱う

### 3.2 EG-Space 的な意味

CONTEXT_JSON の情報量が小さくても、「この PR は本流サンプルか、定型レポートか、実験か」といった **役割の座標** は十分に推定できることが確認できた。

今後は、この分類結果をもとに：

- u_contract 系 PR の整理（auto-merge / sample / cleanup）のパターン化
- PR 山全体に対して同様の射影を行う

ことで、PR 空間に対する EG-Space の理解（C/G/δ）を高いレベルで保ちつつ、詳細は個別 Evidence やログに任せる運用が可能になる。

## 4. 「最低限の解像度ライン」が見えたことの意味

M2 の実験を通じて、以下のような「最低限の解像度ライン」が一つ見えた。

- CONTEXT_JSON:
  - run / PR それぞれに対して、**代表的な ID / パス / ステータス / タイムスタンプ** があれば十分
- North Star 更新:
  - STATE には「代表 run / PR」を 1 行要約で残す
  - メモリには「最小限の厳密さ（時刻や id の正確化）」だけを反映
- 詳細な意味付けや長文の説明:
  - Issue や reports/** に任せる

このバランスであれば、

- LLM の理解が破綻せず、
- 人間も追える形で EG-Space の C/G/δ をトラッキングできる

ことが確認できた。

今後、プロジェクト特性（内容やスケール）に応じて CONTEXT_JSON と North Star の解像度は調整し続ける必要があるが、本メモのラインは「M2 時点の実証済みな初期値」として再利用できる。

## M2 / u_contract persist-report lane (2025-11-16)

- `u_contract_policy v1` の `persist-report` カテゴリを、実 PR #742 / #737 / #684 で検証。
- Codex がラベル `u_contract:persist-report` とコメントを付与し、人間側で `reports/**` のみ変更＋CI Green を確認したうえで 3 本ともマージ。
- この条件（`reports/**` のみ＋CI Green）であれば、M2 フェーズでは「Codex による整理 → 人間の 1 クリック運用」で回せることを確認した。

## M2 / metrics-echo follow-up (plan-only /ask)

- metrics-echo は Phase 2 / M2 で手動 Evidence に基づく `/ask update_north_star` を実行したが、state_patch/memory_patch は出ず plan-only で終了。監視設計と Evidence 形式を Phase 3 以降の宿題とし、詳細設計を `docs/memory/metrics_echo_design.md` にまとめた。
