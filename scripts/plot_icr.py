#!/usr/bin/env python3
import sys
import csv
import matplotlib.pyplot as plt

if len(sys.argv) < 3:
    print("usage: plot_icr.py <icr_history.csv> <out.png>")
    sys.exit(1)

csv_path, out_png = sys.argv[1], sys.argv[2]
ts, vals = [], []
try:
    with open(csv_path, newline="", encoding="utf-8") as f:
        for t, v in csv.reader(f):
            ts.append(t)
            try:
                vals.append(float(v))
            except Exception:
                pass
except FileNotFoundError:
    print(f"CSV file {csv_path} not found, skipping plot")
    sys.exit(0)

if not vals:
    print("no data")
    sys.exit(0)

plt.figure()
plt.plot(range(len(vals)), vals, marker="o")
plt.title("ICR Trend")
plt.xlabel("Runs")
plt.ylabel("ICR (%)")
plt.grid(True)
plt.tight_layout()
plt.savefig(out_png)
print(f"wrote {out_png}")
