# Step 3 Plan Suggester

## 目的
- inventory / STATE / decisions をもとに、DoD と検証観点を含む next_actions.json を生成する。
- CLI (`cli.py plan`) と Streamlit UI の双方で共通ロジック（rule/LLM）を使用する。
- sources を必ず列挙し、不整合はルール合成へフォールバックする。

## 使い方
    python cli.py plan
    python cli.py plan --ai --limit 7
    python cli.py plan --out tmp/next_actions.json

## ルールスコア
- スコア = criticality + deadline + (4 - effort) + risk。
- criticality: H=3 / M=2 / L=1。
- deadline: 期限が近いほど高スコア（<=7日:4, <=30日:3, <=90日:2, それ以外:1, 期限超過:5）。
- effort: S=3 / M=2 / L=1（小さいほど優先）。
- risk: High=3 / Med=2 / Low=1。

## ガード
- inventory の SAMPLE-* 行は常に除外。
- --ai は ask_openai_json を使用し、sources が検証エラーなら即座にルール結果へ戻す。
- plan 生成時に out/next_actions.json（または --out 指定先）へ保存し、CLI/UI はエラーで落ちない。

## 出力例（抜粋）
    {
        "short_goal": "P2-2: Hello KService READY=True",
        "next_actions": [
            {
                "id": "ASSET-001",
                "title": "Rehost: KPI Dashboard",
                "priority": 1,
                "DoD": ["件数一致 ±0.1%", "主要KPI差分 <= 0.5%", "BIスクショ差分 OK"],
                "owner": "owner_a",
                "due": "2025-10-31",
                "links": ["PR #123"],
                "sources": ["inventory/inventory.csv", "reports/decisions/D-20251018-001.yml", "STATE/current_state.md"]
            }
        ]
    }

- 保存先: `out/next_actions.json`
- UI の「診断→優先度」でも同じ JSON が表示されます。
