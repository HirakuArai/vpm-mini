#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="diagrams/src"
OUT_DIR="diagrams/export"

mkdir -p "$OUT_DIR"

echo "=== Mermaid diagrams export start ==="
for file in "$SRC_DIR"/*.md; do
  name=$(basename "$file" .md)
  echo "Converting $file -> $OUT_DIR/${name}.svg"
  mmdc -i "$file" -o "$OUT_DIR/${name}.svg"
done
echo "=== Export complete. Files in $OUT_DIR ==="
