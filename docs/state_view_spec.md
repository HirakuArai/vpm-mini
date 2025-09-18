# State View Specification

## 概要
`scripts/state_view.py` は STATE/<project>/current_state.md を機械可読から人間可読な Markdown レポートに変換し、現在地(C) / ゴール(G) / 差分(δ) / 次アクションを自動出力します。

## プロジェクト命名空間

### 概念
複数プロジェクトの STATE とレポートを明確に分離し、誤混在を防ぐための命名空間システム。

### ディレクトリ構造
```
STATE/
├── vpm-mini/
│   └── current_state.md
├── other-sample/
│   └── current_state.md
└── project-name/
    └── current_state.md

reports/
├── vpm-mini/
│   ├── state_view_20250919_1234.md
│   └── autopilot_results_*.json
├── other-sample/
│   └── state_view_20250919_1235.md
└── project-name/
    └── state_view_20250919_1236.md
```

### 命名規約
- **プロジェクト名**: kebab-case（例: `vpm-mini`, `other-sample`）
- **デフォルトプロジェクト**: `vmp-mini`
- **ディレクトリ名**: プロジェクト名と完全一致
- **レポート出力**: `reports/<project>/` 下に格納

## 入力/出力

### 入力
- **デフォルト**: `STATE/<project>/current_state.md` （project=vpm-mini）
- **プロジェクト指定**: `--project <name>` でプロジェクト切り替え
- **カスタム**: `--in <path>` で任意ファイル指定可能
- **形式**: Markdown ファイル（key: value 形式または見出し＋箇条書き）

### 出力
- **デフォルト**: `reports/<project>/state_view_YYYYMMDD_HHMM.md`
- **カスタム**: `--out <path>` で任意パス指定可能
- **形式**: 構造化された Markdown レポート

## 抽出キー

スクリプトは以下のキーを STATE ファイルから抽出します：

### 必須キー
1. **active_repo**: 作業中のリポジトリ名
2. **active_branch**: 作業中のブランチ名
3. **phase**: 現在のフェーズ（例: "Phase 2"）
4. **context_header**: コンテキスト情報
5. **short_goal**: 短期目標
6. **exit_criteria**: 完了条件（箇条書き可）
7. **優先タスク**: 実行すべきタスク一覧（箇条書き可）

### 抽出形式
#### key: value 形式
```markdown
active_repo: vpm-mini
active_branch: main
phase: Phase 2
```

#### 見出し＋箇条書き形式
```markdown
## 優先タスク
- タスク1の説明
- タスク2の説明
- タスク3の説明
```

## 出力構成

生成される Markdown レポートは以下の構造を持ちます：

### 1. 現在地 (C)
```markdown
# 現在地 (C)
- repo: `vpm-mini`
- branch: `main`
- phase: **Phase 2**
- context: repo=vpm-mini / branch=main / phase=Phase 2
```

### 2. ゴール (G)
```markdown
# ゴール (G)
- short_goal: プロジェクトの短期目標
- exit_criteria:
  - 完了条件1
  - 完了条件2
  - 完了条件3
```

### 3. 差分 (δ)
```markdown
# 差分 (δ)
- 未達Exitの補充・検証を優先
- 優先タスクを先頭から実行し証跡化
```

### 4. 次アクション（最大3件）
```markdown
# 次アクション（最大3件）
- 優先タスク1
- 優先タスク2
- 優先タスク3
```

### 5. メタデータ
```markdown
---
Generated: YYYY-MM-DD HH:MM:SS
Project: vpm-mini
Source: STATE/vpm-mini/current_state.md
Total tasks: N
```

## エラー処理

### プロジェクト命名空間不存在時
- プロジェクト名と利用可能なプロジェクト一覧を表示
- 終了コード 1 で終了
- 例: `[state-view] project namespace not found: other-sample`

### 必須キー欠損時
- 欠損したキー名を標準エラー出力に表示
- 終了コード 1 で終了（CI で検知可能）

### ファイル不存在時
- エラーメッセージを標準エラー出力に表示
- 終了コード 1 で終了

### 成功時の出力例
```
[state-view] reading: STATE/vpm-mini/current_state.md
[state-view] file size: 1234 chars, 56 lines
[extract] active_repo: vpm-mini
[extract] active_branch: main
[extract] phase: Phase 2
[extract] context_header: repo=vpm-mini / branch=main / phase=Phase 2
[extract] short_goal: プロジェクトの目標説明
[extract] exit_criteria: 3 items
[extract] 優先タスク: 5 items
[state-view] written: reports/vpm-mini/state_view_20250919_0615.md (1456 chars)
[state-view] extracted keys: active_repo, active_branch, phase, context_header, short_goal, exit_criteria, 優先タスク
```

## 使用方法

### コマンドライン実行
```bash
# デフォルト設定で実行（vpm-mini プロジェクト）
python3 scripts/state_view.py

# プロジェクト指定で実行
python3 scripts/state_view.py --project other-sample

# プロジェクト + カスタム出力ファイル指定
python3 scripts/state_view.py --project my-project --out reports/my-project/custom_report.md

# カスタム入力ファイル指定（プロジェクト命名空間バイパス）
python3 scripts/state_view.py --in custom_state.md --out custom_report.md

# ヘルプ表示
python3 scripts/state_view.py --help
```

### Makefile 経由
```bash
# 標準実行
make state-view
```

### GitHub Actions
```bash
# 手動実行ワークフロー
# Actions タブ → "state-view" → "Run workflow"
```

## 運用方針

### PR作成時の使用
1. PR作成前に `make state-view` を実行
2. 生成されたレポートを Evidence として PR に添付
3. 以後の判断・修正はこのレポートを根拠とする

### 会話のSSOT (Single Source of Truth)
- 現在の状況把握の統一基準
- 次のアクション決定の根拠
- 進捗確認とゴール設定の基盤

## ファイル依存関係

### 入力依存
- `STATE/current_state.md` （または指定ファイル）

### 出力生成
- `reports/p2_state_view_*.md`

### ディレクトリ自動作成
- `reports/` ディレクトリが存在しない場合は自動作成

## 技術仕様

### 言語・環境
- Python 3.x
- 標準ライブラリのみ使用（外部依存なし）

### 文字エンコーディング
- 入力/出力共に UTF-8

### 正規表現パターン
- key: value 抽出: `^{key}\s*:\s*(.+)$`
- 見出し抽出: `^#+\s*{key}[^\n]*\n((?:- .+\n?)+)`

## バージョン情報

- **Version**: 1.0
- **Author**: Generated from specification
- **License**: Same as project license