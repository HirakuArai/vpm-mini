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

# Check if docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo "[healthcheck] ERROR: docker command not found"
  exit 1
fi

# Check compose config
if ! docker compose config -q; then
  echo "[healthcheck] ERROR: docker compose config validation failed"
  exit 1
fi

echo "[healthcheck] OK"