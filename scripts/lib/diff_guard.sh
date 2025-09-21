#!/usr/bin/env bash
set -euo pipefail
# Usage: diff_guard.sh <patchfile> "<glob1,glob2,...>" <max_lines>
PATCH="$1"
ALLOWLIST="$2"
MAX="$3"

# 空/不存在パッチは失敗にしない（呼び元で扱う）
[[ -s "$PATCH" ]] || { echo "[guard] empty patch"; exit 0; }

# 変更ファイル抽出
mapfile -t FILES < <(grep -E '^(\+\+\+|---) ' "$PATCH" | sed -E 's@^[+-]{3} @@' | sed 's@^a/@@; s@^b/@@' | sort -u)

# allowlist 判定（bash の extglob ではなく grepで簡易実装）
IFS=',' read -r -a GLOBS <<< "$ALLOWLIST"
allow_ok=true
for f in "${FILES[@]}"; do
  hit=false
  for g in "${GLOBS[@]}"; do
    # glob → 正規表現（* → .*)
    regex="^${g//\*/.*}$"
    [[ "$f" =~ $regex ]] && { hit=true; break; }
  done
  $hit || { echo "[guard] deny: $f"; allow_ok=false; }
done
$allow_ok || { echo "[guard] allowlist violation"; exit 22; }

# 追加行カウント（'+++'ヘッダ除外、コード追加のみ）
ADDED=$(grep -E '^\+[^+]' "$PATCH" | wc -l | awk '{print $1}')
echo "[guard] added_lines=$ADDED (max=$MAX)"
[[ "$ADDED" -le "$MAX" ]] || { echo "[guard] change too large"; exit 23; }

echo "[guard] patch validation passed"
exit 0