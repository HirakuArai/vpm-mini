#!/usr/bin/env bash
set -euo pipefail

PKGS="git python3-pip python3-venv jq gh docker.io tmux python3-requests"
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y $PKGS
fi

sudo usermod -aG docker "$USER" || true

REPO_DIR="$HOME/vpm-mini"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone https://github.com/HirakuArai/vpm-mini.git "$REPO_DIR"
fi

ENVF="$HOME/.codex_env"
mkdir -p "$(dirname "$ENVF")"
# REPO を env に書く（無ければ追記）
grep -qx 'export REPO=HirakuArai/vpm-mini' "$ENVF" 2>/dev/null || echo 'export REPO=HirakuArai/vpm-mini' >> "$ENVF"

# GH_TOKEN を対話で一度だけ
if ! grep -q '^export GH_TOKEN=' "$ENVF" 2>/dev/null; then
  echo -n "Paste fine-grained GH_TOKEN: "
  read -r GH_TOKEN
  echo "export GH_TOKEN=$GH_TOKEN" >> "$ENVF"
fi

# loginシェルで env を読む設定を冪等に
grep -qx 'source ~/.codex_env' "$HOME/.bashrc" 2>/dev/null || echo 'source ~/.codex_env' >> "$HOME/.bashrc"
# shellcheck disable=SC1090
source "$ENVF"

# systemd user unit 配置
mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$REPO_DIR/tools/systemd/codex-worker.service" "$HOME/.config/systemd/user/codex-worker.service"

# linger & 起動
loginctl enable-linger "$USER" || true
systemctl --user daemon-reload
systemctl --user enable --now codex-worker

echo "[OK] codex-worker started. Check:"
echo "systemctl --user status codex-worker --no-pager || journalctl --user -u codex-worker -n 200 --no-pager"
