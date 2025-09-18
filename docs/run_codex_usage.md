# run_codex Usage Guide

## 概要
`run_codex.sh` は task.json を読み込み、Claude Code または codex CLI で実行するハンドオフスクリプトです。

## ローカル実行

### 前提条件
- `jq` コマンドがインストールされていること
- `ops/agent_handoff/task.json` が存在すること

### 基本的な使い方
```bash
# 1. task.json を作成
cat > ops/agent_handoff/task.json <<'EOF'
{
  "meta": {
    "dry_run": true,
    "use_codex": false
  },
  "task": {
    "description": "List YAML files in infra directory",
    "command": "find infra -name '*.yaml' -o -name '*.yml' | wc -l"
  }
}
EOF

# 2. スクリプトを実行
./ops/agent_handoff/run_codex.sh

# 3. クリップボードから Claude Code に貼り付けて実行
```

### codex CLI を使う場合
```bash
# meta.use_codex を true に設定
jq '.meta.use_codex = true' ops/agent_handoff/task.json > tmp.json && mv tmp.json ops/agent_handoff/task.json

# 実行（codex がインストールされている場合のみ）
./ops/agent_handoff/run_codex.sh
```

## CI での実行

### GitHub Actions Workflow
```yaml
# .github/workflows/run_codex.yml
name: Run Codex Manual
on:
  workflow_dispatch:
    inputs:
      prompt_file:
        description: 'Prompt file path'
        required: false
        default: 'prompts/interpret_sample.md'
```

### 手動トリガー
1. Actions タブを開く
2. "Run Codex Manual" を選択
3. "Run workflow" をクリック
4. prompt_file を指定（デフォルト: prompts/interpret_sample.md）

## Evidence フォーマット

### 標準的な Evidence 構造
```markdown
# Codex Run Evidence
- datetime(UTC): YYYY-MM-DDTHH:MM:SSZ
- run_id: run_YYYYMMDD_HHMMSS
- dry_run: true/false
- status: ok/error

## Input
- task.json path: ops/agent_handoff/task.json
- prompt: [実行したプロンプトまたはタスク]

## Output
```
[実行結果の要約]
```

## Verification
- [ ] スクリプトが正常終了
- [ ] ログファイルが生成された
- [ ] スナップショットが保存された
```

## トラブルシューティング

### よくあるエラーと対処法

#### 1. jq not found
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

#### 2. task.json not found
```bash
# ファイルが存在するか確認
ls -la ops/agent_handoff/task.json

# サンプルを作成
echo '{"meta":{"dry_run":true},"task":{}}' > ops/agent_handoff/task.json
```

#### 3. Permission denied
```bash
# 実行権限を付与
chmod +x ops/agent_handoff/run_codex.sh
```

#### 4. pbcopy not found (Linux)
```bash
# xclip を使用
alias pbcopy='xclip -selection clipboard'

# または xsel を使用
alias pbcopy='xsel --clipboard --input'
```

#### 5. ログファイルが空
- task.json の内容を確認
- dry_run モードで実行してみる
- codex CLI がインストールされているか確認

## 出力先

### ファイルとディレクトリ
- **スナップショット**: `ops/agent_handoff/history/task_YYYYMMDD_HHMMSS.json`
- **実行ログ**: `reports/codex_run_YYYYMMDD_HHMMSS.log`
- **メタデータ**: `ops/agent_handoff/task_runs.ndjson` (追記型)
- **最新インデックス**: `reports/_latest_index.md`
- **シンボリックリンク**: `ops/agent_handoff/history/latest.json`

### クリーンアップ
```bash
# 古いログを削除（30日以上前）
find reports -name "codex_run_*.log" -mtime +30 -delete

# 履歴をアーカイブ
tar czf history_backup.tar.gz ops/agent_handoff/history/
```

## ベストプラクティス

1. **task.json のバージョン管理**
   - 重要なタスクはスナップショットを Git にコミット
   - センシティブな情報は含めない

2. **dry_run の活用**
   - 本番実行前は必ず dry_run = true でテスト
   - 影響を確認してから実行

3. **Evidence の保存**
   - CI 実行時は必ず artifacts に保存
   - ローカル実行時も reports/ に保存

4. **エラーハンドリング**
   - status が error の場合はログを確認
   - 失敗時は task_runs.ndjson で履歴を追跡