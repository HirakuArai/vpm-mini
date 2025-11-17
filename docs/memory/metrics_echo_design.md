# metrics-echo Design Memo (Draft)

context_header: repo=vpm-mini / branch=main / phase=Phase 2→3

## 1. 現状整理（Phase 2 / M2 時点）

- dev overlay に Knative Service 定義が存在:
  - `infra/k8s/overlays/dev/metrics-echo-ksvc.yaml`
- Phase 2 / M2 では、手動の ready-check テキストを Evidence として、Issue #764 経由で `/ask update_north_star` を 1 回実行した。
- ask-entry run 自体は success だったが、
  - `state_patch` / `memory_patch` は出ず、
  - plan / warnings のみ（plan-only）という結果だった。
- このため、Phase 2 / M2 の出口としては、
  - **「現状の Evidence では North Star を固定しない」**
  - **「監視設計と Evidence 形式を整理したうえで後続フェーズで再チャレンジする」**
 という方針になっている。

このメモは、その「後続フェーズでの再チャレンジ」のための設計メモである。

---

## 2. 目指す North Star（案）

metrics-echo の North Star（サービスとして「良い状態」）を、最初はシンプルな指標に絞って定義する。

例（案）:

- KService `metrics-echo` が `READY=True` で安定していること
- 一定期間（例: 直近 N 分〜数時間）の HTTP リクエストに関して:
  - 成功率が X% 以上
  - 異常なエラーが継続していない
- 必要に応じて、レイテンシ（P50 / P95 など）も将来的な North Star 候補とする。

Phase 3 の前半では、まずは:

- `READY=True` 継続
- HTTP 成功率

といった基本的な SLI を North Star の中心に据え、詳細なレイテンシやコスト最適化は Phase 4 以降の拡張とする。

---

## 3. 必要な Evidence の種類とフォーマット

`/ask update_north_star` に渡す CONTEXT を設計するため、どの Evidence をどのフォーマットで残すかを整理する。

候補:

1. **Knative Service status**
   - 取得元: `kubectl get ksvc metrics-echo -o yaml` または `-o json`
   - 内容: READY 状態、Conditions、URL など
   - 利用方法: CONTEXT_JSON 内の `kservice_status` フィールドとして要約を渡す。

2. **HTTP 成功率 / エラー率**
   - 取得元: Prometheus / Grafana（既存のメトリクスライン）
   - 形式:
     - PNG: 直近 N 分〜数時間の成功率・エラー率グラフ
     - MD/JSON: 集計値（成功率 %, リクエスト数、エラー数）
   - 利用方法: `sli_summary` として要約し、必要なら PNG への参照を含める。

3. **レイテンシ（将来追加予定）**
   - P50 / P95 などのレイテンシ統計。
   - Phase 3 では「参考情報」として扱い、Phase 4 以降に North Star の一部へ昇格させる。

Evidence の保存場所:

- `reports/metrics-echo/**` 配下に
  - PNG（Grafana レンダリング）
  - MD（集計結果）
  - JSON（機械可読な SLI サマリ、必要なら）
  をまとめるイメージ。

---

## 4. /ask CONTEXT 設計案

`/ask update_north_star` に渡す CONTEXT_JSON には、最低限次のキーを含めることを目標とする。

- `kservice_status`
  - READY 状態 / Conditions の要約
- `sli_summary`
  - 直近の成功率 / エラー率 / リクエスト数など
- `evidence_paths`
  - `reports/metrics-echo/**` 配下の PNG / MD / JSON への相対パス一覧
- `recent_issues`（任意）
  - 最近の障害・インシデントに関する Issue 番号や概要

これにより、/ask 側は:

- 現在のヘルス状態
- Evidence ファイルの場所
- 既知の問題

を踏まえたうえで、North Star の更新や plan-only 判断を行える。

---

## 5. フェーズ分割案（Phase 3 〜 4）

Phase 3:

- `metrics_echo_design.md` に基づき、
  - READY チェック
  - HTTP 成功率
  の Evidence 生成パイプを最低限構築する。
- CONTEXT_JSON に `kservice_status` と `sli_summary` を含めた形で、
  再度 `/ask update_north_star` を実行する（必要なら plan-only でもよい）。

Phase 4 以降:

- レイテンシやコスト指標を SLI/SLO として整理し、
  - North Star への組み込み
  - セル横断での最適化（他セルとのトレードオフ）
- 必要に応じて、自動アラートや Self-Cost セルとの連携も検討する。

---

## 6. 今後の扱い

- metrics-echo は、Phase 2 / M2 では「plan-only の /ask を 1 回実行し、North Star 固定は見送ったセル」として扱う。
- Phase 3 以降は、このメモを起点に:
  - 監視 / Evidence ラインを整備し、
  - 適切なタイミングで /ask を再実行し、
  - 必要なら North Star と STATE / EG-Space を更新する。

このメモ自体は、Phase 3 の途中で更新・拡張されることを前提としたドラフトである。

---

## P3-2 READY Evidence snapshot (Phase 3)

- READY snapshot PR: #778  
  - 追加ファイル: `reports/metrics-echo/metrics_echo_ready_status_p3-2.md`  
  - 内容: `kubectl -n <namespace> get ksvc metrics-echo -o yaml` の生出力を Markdown レポートとして保存。
- 上記レポートは、Issue #774 (P3-2: metrics-echo minimal SLI /ask retry) における
  「READY 側 Evidence」の第一ステップとして扱う。

---

## P3-2 SLI minimal design (Draft)

- 対象期間（暫定）:
  - 直近 60 分程度を想定（初回は「last 60 minutes」を目安とする）。
- 指標（最小セット）:
  - HTTP 成功率:
    - 2xx / 全リクエスト数（0〜100%）
  - リクエスト総数:
    - 対象期間中の全リクエスト数
  - エラー数:
    - 対象期間中のエラー（例: 5xx）件数

- Evidence ファイル案:
  - パス: `reports/metrics-echo/metrics_echo_sli_p3-2.md`
  - 内容イメージ:
    - 取得時刻（例: ISO8601 / ローカル時刻）
    - 対象期間（例: "last 60 minutes"）
    - 成功率 [%]
    - リクエスト数（total）
    - エラー数（error count）

- 備考:
  - P3-2 では、まずは「READY + この最小 SLI」を Evidence として揃えたうえで、
    `/ask update_north_star` の再実行を行う。
  - SLI の定義や対象期間は、Phase 3 の運用状況を見ながら
    Phase 4 以降で SLO 設計に昇格させることを想定している。
