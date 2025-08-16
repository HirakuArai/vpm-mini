#!/usr/bin/env bash
set -euo pipefail
pytest -q || exit 1
# 図のエクスポートは任意（Mermaid未導入でもfailにしない）
./scripts/export_diagrams.sh || true