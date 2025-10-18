# Step 1 Grounded Q&A

## 目的
- SSOT（STATE / inventory / decisions / reports）の抜粋だけを根拠に回答する。
- 既存 CLI (`cli.py`) と Streamlit UI から同じ grounded_answer() を呼び出す。
- sources / confidence / unknown_fields を含む JSON 出力で整合性を確認する。

## 使い方
    export OPENAI_API_KEY=...  # 任意（キーが無い場合はルール回答にフォールバック）
    python cli.py answer "今のPhaseは？"
    python cli.py answer --ai "進捗は？ High残は？"
    streamlit run apps/vpm_decision_demo_app.py

## ガード
- LLM モードは SSOT 抜粋と質問文だけで回答し、仮説は `仮説:` で明示する。
- sources はリポジトリ相対パス（任意で :Lx-Ly）を返し、verify_sources() で存在を確認する。
- sources 検証に失敗した場合は answer を「不足」にフォールバックし confidence を 0.3 以下に下げる。
- レポジトリの既存 Markdown フェンスは変更せず、新規ドキュメントはインデント表記を採用する。
