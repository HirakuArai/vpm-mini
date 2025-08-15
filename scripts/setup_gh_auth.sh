#!/bin/bash
# GitHub CLI 認証セットアップスクリプト（PAT使用）

set -euo pipefail

echo "================================================"
echo "GitHub CLI 認証セットアップ (Personal Access Token)"
echo "================================================"
echo ""
echo "事前準備："
echo "1. GitHub.com で Personal Access Token (PAT) を作成"
echo "   Settings → Developer settings → Personal access tokens"
echo "2. 必要なスコープ: repo, workflow"
echo "3. トークンをコピー"
echo ""
echo "================================================"
echo ""

# トークン入力を促す
read -sp "GitHub Personal Access Token を入力してください: " GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "エラー: トークンが入力されていません"
    exit 1
fi

# 環境変数設定
export GITHUB_TOKEN="$GITHUB_TOKEN"
export GH_TOKEN="$GITHUB_TOKEN"

echo "認証を実行中..."

# gh auth login with token
printf "%s" "$GITHUB_TOKEN" | gh auth login --hostname github.com --with-token

# 認証状態確認
echo ""
echo "認証状態:"
gh auth status -t

echo ""
echo "✅ 認証が完了しました"
echo ""
echo "今後のセッションでも使用する場合は、以下を実行してください："
echo "export GITHUB_TOKEN='YOUR_TOKEN'"
echo "export GH_TOKEN=\$GITHUB_TOKEN"