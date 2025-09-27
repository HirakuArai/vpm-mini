# EG-Space × ICR デモ（LLMフォールバック付き）

## 前提
- どちらかの環境変数を設定：
  - `export ANTHROPIC_API_KEY=...` または `export OPENAI_API_KEY=...`

## 実行
```bash
./scripts/gen_report.sh STATE/mna_state.md
```

## 生成物
- `reports/mna_update_YYYYMMDD_HHMM.md` … EG-Space / ICR / 次の一手（LLM生成）
- `reports/icr_history.csv` … 実行ごとの ICR 変化ログ
- `reports/icr_history.png` … ICR 推移の簡易グラフ

## トラブルシュート
- **LLMキー未設定** → `codex_shim.py` がエラー終了。キーを設定し再実行。
- **グラフが描けない** → CSVが空の場合。最低1回はレポート生成が必要。
- **Python依存パッケージ不足** → `pip install anthropic openai matplotlib`

## 仕組み
1. `gen_report.sh` が `codex` コマンドの有無を確認
2. なければ `codex_shim.py` にフォールバック（LLM API使用）
3. ICR値を抽出して `icr_history.csv` に追記
4. `plot_icr.py` で推移グラフを生成

## デモシナリオ
1. 初回実行: `IT-02` が `in_prog` (0.5) の状態で実行 → ICR: 約47%
2. タスク更新: `STATE/mna_state.md` で `IT-02` を `done` (1.0) に変更
3. 再実行: ICR が約55%に上昇することを確認
4. グラフ確認: `reports/icr_history.png` に推移が記録される