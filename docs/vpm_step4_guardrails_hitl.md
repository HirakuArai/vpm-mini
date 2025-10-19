# Step 4 Guardrails & HITL

## 目的
- Step1〜3 の成果物（Q&A JSON / plan JSON / state Markdown）を自動検証し、壊れない運用を担保する。
- CLI と UI に HITL ガードを加え、AI出力が検証NGのときは即座にルール出力へ差し戻せるようにする。

## 使い方（CLI）
    python cli.py validate --type answer --file out/answer.json
    python cli.py validate --type plan --file out/next_actions.json
    python cli.py validate --type state --file STATE/update_*.md

- OK / NG を標準出力に表示します。NG 時は理由を箇条書きで出力します。

## UI での HITL
- サイドバーに検証スイッチ（Q&A / Plan / STATE）を追加。デフォルト ON。
- Q&A/Plan/STATE の各出力は検証結果（OK/NG）がバッジ表示され、NG のときは理由が列挙されます。
- AIモードで NG の場合は「ルール版に差し戻す」ボタンを押すと即ルール出力へ切り替わります。
- 検証結果は `reports/events/validation_YYYYMMDD_HHMMSS.yml` に記録されます。

## sources 検査
- sources は `inventory/inventory.csv` や `reports/decisions/D-*.yml` など repository 相対パスを要求します。
- verify_sources が実在性をチェックし、:Lx-Ly の行指定があれば範囲検査を行います（指定は任意）。

## HITL 運用ルール
- **NG の場合は差し戻す**: UI のボタン、または CLI で `--ai` を外して再生成してください。
- **承認は PR で記録**: DoD として最新の検証ログ（validation_*.yml）のパスを PR 本文に添付します。
- **AI は常に任意**: キー未設定／検証NG の場合は自動でルール合成へフォールバックします。
