# VPM Entry Point (unified)
- **CLI**: `scripts/vpm --mode decide --in <input.md> --out <output.md>`
- **Resolution**:
  1) If `scripts/codex_shim.py` exists → delegate
  2) Else if `scripts/vpm_engine.py` exists → delegate
  3) Else → stub fallback (雛形の推奨を出力)
- **I/O**: 作業I/Oは `.vpm/` に置き、Gitには載せない（ローカル専用）
- **今後**: `scripts/vpm_engine.py` を実装すれば差し替え可能（スイッチ不要）
