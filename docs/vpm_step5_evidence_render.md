# Step 5 Evidence Render Stabilization

## スケジュールと実行条件
- `render_grafana_png.yml` は JST 07:00（UTC 22:00）の cron で起動します。
- `workflow_dispatch` で `from` / `to` を指定した手動実行も可能です（未指定時は過去24時間）。
- concurrency: `render-grafana-png-${ref}`、`cancel-in-progress: true`
- timeout: 20 分
- permissions: `contents: write`, `actions: read`

## 検証フッタ
- レンダ後に `reports/img/grafana_*.png` / `reports/*_grafana_render_*.md` を検証します。
- 条件
  - `grafana_p4-uptime-blackbox_*.png` が存在
  - `grafana_vpm-basic-observability_*.png` が存在
  - Evidence MD が 2 件以上
- 検証結果は `evidence_footer.txt` に集約され、PR コメントに `## Validate` セクションとして追記されます（NG があれば `NG:` で明示）。
- `reports/events` などへの追加は不要です。

## 手動トリガーの例
    gh workflow run render_grafana_png.yml -f from=now-30m -f to=now

- range を省略した場合は `now-24h → now` が使用されます。
- 手動実行でも同じ検証フッタと PR コメントが生成されます。

## 失敗時の扱い
- NG が検出されてもワークフローは失敗させず、PR コメントとログで可視化します。
- 追加の通知（Slack/Webhook など）は今後の拡張で対応します。
