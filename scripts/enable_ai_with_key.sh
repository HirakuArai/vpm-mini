#!/bin/bash
# .env の OPENAI_API_KEY を読み込んで Secret を作り直し → AI を有効化 → 実コール確認
set -euo pipefail
NS=hyper-swarm
APP=hello-ai
ENV_FILE="/Users/hiraku/projects/vpm-mini/.env"

# 1) .env から OPENAI_API_KEY を取り出す（余計なキーはアップしない）
set -a
source "$ENV_FILE"
set +a
[[ "${OPENAI_API_KEY:-}" == sk-* ]] || { echo "[x] .env に有効な OPENAI_API_KEY がありません"; exit 1; }

# 2) Secret を更新（冪等）
kubectl -n "$NS" delete secret openai-secret --ignore-not-found
kubectl -n "$NS" create secret generic openai-secret \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY"

# 3) AI を有効化して再デプロイ
kubectl -n "$NS" patch configmap hello-ai-cm --type merge -p '{"data":{"AI_ENABLED":"true"}}'
kubectl -n "$NS" rollout restart ksvc/$APP || true
kubectl -n "$NS" wait ksvc/$APP --for=condition=Ready --timeout=180s

# 4) 実コール（X-Fallback:false で成功判定）
URL_HOST=$(kubectl -n "$NS" get ksvc $APP -o jsonpath='{.status.url}' | sed -E 's#^https?://##')
kubectl -n kourier-system port-forward svc/kourier 8080:80 >/tmp/pf_hello_ai.log 2>&1 &
PF=$!; trap "kill $PF 2>/dev/null || true" EXIT; sleep 2
RESP=$(curl -isS -H "Host: ${URL_HOST}" 'http://127.0.0.1:8080/hello-ai?msg=ping' | tee /tmp/resp.txt)
XF=$(grep -i '^X-Fallback:' /tmp/resp.txt | awk -F': ' '{gsub(/\r/,"",$2); print tolower($2)}' | tail -n1)
echo "X-Fallback=${XF}"

# 5) 判定
if [[ "$XF" == "false" ]]; then
  echo "[✓] AI 有効化成功: X-Fallback=false"
  exit 0
else
  echo "[x] AI 有効化失敗: X-Fallback=${XF}"
  exit 1
fi