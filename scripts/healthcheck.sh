#!/usr/bin/env bash
set -euo pipefail

echo "[healthcheck] start"

# S1: compose 前なので存在しなくてOK。なければ成功で抜ける。
if [[ ! -f "compose.yaml" ]]; then
  echo "[healthcheck] compose.yaml not found; S1 stage -> skip docker checks and exit 0"
  exit 0
fi

# ここから先は S2+ 用（存在するときのみ実行）
echo "[healthcheck] compose.yaml found -> running docker sanity"
docker compose config -q
echo "[healthcheck] OK"