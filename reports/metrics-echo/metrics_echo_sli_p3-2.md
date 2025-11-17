# metrics-echo SLI Snapshot (P3-2 / Phase 3)

context_header: repo=vpm-mini / branch=main / phase=Phase 3 / track=P3-2 metrics-echo

本レポートは、Issue #774 (P3-2: metrics-echo minimal SLI /ask retry) に向けて、
metrics-echo に対して連続 HTTP リクエストを投げた結果から、最小限の SLI を算出したスナップショットである。

## 1. Measurement summary

- 取得時刻 (UTC): `2025-11-17T00:53:01Z`
- 対象期間: 即時（連続 20 リクエスト）
- 成功率 (HTTP 200): `0%`
- リクエスト数 (total): `20`
- エラー数 (non-200): `20`

## 2. 測定方法メモ

- KService status.url: `http://metrics-echo.default.127.0.0.1.nip.io` (namespace: `default`)
- 測定方法:
  - bash から `curl` を 20 回連続実行し、HTTP ステータスコードを集計。
  - 200 を成功、それ以外をエラーとしてカウント。

## 3. 備考

- 本レポートは P3-2 における「最小 SLI」の暫定実装として扱う。
- 今後、Prometheus ベースの SLI / SLO 設計に移行する際のたたき台とする。
