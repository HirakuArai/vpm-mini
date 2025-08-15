# vpm-mini

P0-2 GREEN: 要約Pipeline実装プロジェクト

## 10分で再現する — 要約Pipeline (P0-2)

このプロジェクトには、会話ログから **≤400字の要約** を生成し、`memory.json` の**先頭に追記**する Pipeline が実装されています。以下の手順で、ローカル環境で10分以内に動作を再現できます。

### 前提条件

* **Python** 3.10 以上
* **Node.js** v20.x（固定）
* Mermaid CLI（`mmdc`）は図の書き出しを行う場合のみ必要

### セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/HirakuArai/vpm-mini.git
cd vpm-mini

# 2. （任意）仮想環境を作成
python -m venv .venv && source .venv/bin/activate
```

> このプロジェクトの要約機能は標準ライブラリのみで動作します。追加の pip インストールは不要です。

### サンプル入力の用意

```bash
mkdir -p samples
cat > samples/transcript_ja.txt <<'EOF'
この文章はサンプルの会話ログです。目的や決定事項、次の課題などを含んでいます。…（適当な長文を入れてください）
EOF
```

### 要約Pipelineの実行

```bash
python -m vpm_mini.summary --input samples/transcript_ja.txt
```

実行結果：

* ターミナルに **≤400字の要約** が表示されます
* `memory.json` の先頭に要約文字列が1件追加されます（ファイルがなければ自動生成）

### 結果の確認

```bash
head -n 20 memory.json
```

### （任意）図の書き出し

会話マップなどのMermaid図を `.svg` に変換する場合：

```bash
# Mermaid CLI が必要（npm i -g @mermaid-js/mermaid-cli）
./scripts/export_diagrams.sh
```

* `diagrams/src/*.md` → `diagrams/export/*.svg` に変換されます

---

## セットアップの注意

* `.env` に `GH_TOKEN`（Fine-grained PAT）を設定する場合、必ず `.gitignore` により追跡から除外してください
* `.env.example` を参考にローカル専用 `.env` または `.env.local` を作成

---

## DoD（Definition of Done）

* 上記手順がそのまま通ること
* 要約が **400文字以内** で出力されること
* `memory.json` の先頭に追記されること
* （必要な場合のみ）Mermaid図が正しく出力されること