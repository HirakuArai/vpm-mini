#!/usr/bin/env bash
set -euo pipefail
REP="${1:?usage: append_icr_csv.sh <report.md>}"
CSV="reports/icr_history.csv"
mkdir -p reports
touch "$CSV"

# "ICR: 47.3%" のような行から数値だけ抽出
VAL=$(grep -m1 -Eo 'ICR:\s*[0-9]+(\.[0-9]+)?' "$REP" | awk '{print $2}')
[ -z "${VAL:-}" ] && exit 0

echo "$(date +%Y-%m-%dT%H:%M:%S),$VAL" >> "$CSV"
echo "Appended ICR=$VAL to $CSV"