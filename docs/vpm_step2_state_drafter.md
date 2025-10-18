# Step 2 State Drafter

## 目的
- Decision Log (reports/decisions/*.yml) をもとに STATE/update_YYYYMMDD.md の草案を自動生成する。
- CLI (`cli.py state-update`) からルール合成 or LLM 補助 (--ai) を切り替えられるようにする。
- sources に Decision Log と STATE を列挙し、LLM 失敗時は安全にルール本文へフォールバックする。

## 使い方
    python cli.py state-update
    python cli.py state-update --ai
    python cli.py state-update --ai --decisions-dir /path/to/decisions --print

## ガード
- Decision Log が空の場合でも、STATE/update_YYYYMMDD.md に空テンプレートを生成する。
- --ai オプションは ask_openai_json を使用するが、失敗時はルール本文へフォールバックする。
- sources には reports/decisions/ 以下のファイルと STATE/current_state.md を含める。
