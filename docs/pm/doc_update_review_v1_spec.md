# doc_update_review_v1 Spec
repo=vpm-mini / branch=main  
Phase 2 (PM Kai v1 + Layer B / Reviewer Kai)

doc_update_review_v1 は、**Reviewer Kai が doc_update_proposal_v1 を評価した結果**を表す JSON 形式の SSOT である。

- Proposer Kai の提案 (doc_update_proposal_v1)
- Reviewer Kai の評価 (doc_update_review_v1)
- Human（啓＋ChatGPT）の判断（Accept/Reject）

の 3レイヤーを明確に分離するためのフォーマット。

---

## 1. デザイン方針

- **JSON を SSOT とする**  
  Markdownビューは必要に応じて生成するだけで、原本は常に JSON。
- Reviewer Kai は **ファイルを直接編集しない**。  
  あくまで「提案をどう扱うべきか」のメタ情報を出す。
- Human は JSON を読み、
  - 「この proposal＋review セットを採用してよいか？」を判断する。
  - JSON 自体は原則変更しない。

---

## 2. スキーマ概要

トップレベル構造（v1 の最小形の例）:

    {
      "schema_version": "doc_update_review_v1",
      "project_id": "vpm-mini",
      "proposal_ref": "reports/doc_update_proposals/2025-11-24_vpm-mini.json",
      "generated_at": "2025-11-24T16:30:00+09:00",
    
      "overall_assessment": {
        "summary": "提案内容は目的と整合しており低リスク。STATE と weekly の整合性も保たれる。",
        "risk_level": "low"
      },
    
      "update_judgements": [
        {
          "target_path": "STATE/vpm-mini/current_state.md",
          "section_hint": "1.1 Current",
          "decision": "accept",
          "reason": "Layer B 設計書の追加と hakone-e2 試行の反映は現状を正しく表現しているため。",
          "suggestion_override": null
        }
      ],
    
      "notes": [
        "今回のレビューは、Layer B 設計 v1 と hakone-e2 での試行結果を前提に行った。",
        "高リスクな変更は含まれていないと判断。"
      ]
    }

---

## 3. フィールド定義

### 3.1 メタ情報

- schema_version (string, required)  
  例: "doc_update_review_v1"

- project_id (string, required)  
  例: "vpm-mini", "hakone-e2"

- proposal_ref (string, required)  
  評価対象となる doc_update_proposal_v1 のパス。  
  例: "reports/doc_update_proposals/2025-11-24-vpm-mini.json"

- generated_at (string, required)  
  ISO 8601 形式の生成日時（タイムゾーン付き推奨）。  
  例: "2025-11-24T16:30:00+09:00"

---

### 3.2 overall_assessment

Reviewer Kai による、proposal 全体の評価。

    "overall_assessment": {
      "summary": "提案内容は目的と整合しており低リスク。STATE と weekly の整合性も保たれる。",
      "risk_level": "low"
    }

- summary (string, required)  
  人間が読むことを前提とした要約コメント。

- risk_level (string, required)  
  提案全体のリスクレベル。  
  v1 では以下の 3 値とする：
  - "low": ほぼ自明／誤っても影響が小さい
  - "medium": 内容の妥当性を慎重に見る必要がある
  - "high": 人間の詳細レビューを必須とすべき、または採用は慎重に検討

---

### 3.3 update_judgements[]

doc_update_proposal_v1.updates[] に対する、Reviewer Kai の判断。

    "update_judgements": [
      {
        "target_path": "STATE/vpm-mini/current_state.md",
        "section_hint": "1.1 Current",
        "decision": "accept",
        "reason": "Layer B 設計書の追加と hakone-e2 試行の反映は現状を正しく表現しているため。",
        "suggestion_override": null
      }
    ]

各要素のフィールド：

- target_path (string, required)  
  対象ファイルのパス。  
  doc_update_proposal_v1.updates[i].target.path に対応。

- section_hint (string, optional)  
  対象となるセクションのヒント。  
  例: "1.1 Current", "Next 3" など。  
  Proposer からコピーしてもよいし、Reviewer が補足してもよい。

- decision (string, required)  
  Reviewer Kai による judgement。  
  v1 ではまず以下の 2 値から始める：
  - "accept": 提案通りに適用してよい
  - "reject": 提案は採用すべきでない

  将来拡張として "accept_with_edits" を追加する余地を残す。

- reason (string, required)  
  その judgement に至った理由。Human が判断しやすいように書く。

- suggestion_override (string or null, optional)  
  - v1 では原則 null。  
  - 将来的に "accept_with_edits" を導入する際、
    Proposer の suggestion_markdown を上書きしたいときに使用する。

### 3.4 target_files / final_content（Tsugu apply v1 用）

Tsugu が機械適用する際に参照するフィールド。各ファイルにつき 1 エントリとし、**final_content に適用後の全文を含める**。

- target (object, required)
  - path: STATE/ または docs/ 配下のファイルパス
- change_type (string, required)  
  - v1 は `"replace_whole_file"` のみ
- final_content (string, required)  
  - 適用後の完成形全文。見出しや箇条書きなど既存構造を保った上で、提案を反映した完成形（replace_whole_file の場合はファイル全体が入る）。
- risk (string, required)  
  - `"low"` でないものは Tsugu v1 では適用しない
- reviewer_comment (string, optional)  
  - 補足メモ。auto_accept_v1 では「人間レビュー推奨」などを記載

備考:
- suggestion_markdown や section_hint は参考情報。Tsugu v1 は final_content を使って全置換する。
- 同一 path の複数エントリは持たない（1ファイル1エントリ）。

---

### 3.5 notes[]

Reviewer Kai からの補足メモ。

    "notes": [
      "今回のレビューは、Layer B 設計 v1 と hakone-e2 での試行結果を前提に行った。",
      "高リスクな変更は含まれていないと判断。"
    ]

- 予備条件や前提
- 今後の提案へのフィードバック
- Human が判断するときに知っておくとよい背景

などを自由形式で書く。

---

## 4. 運用上の前提（Phase 2）

- doc_update_review_v1 は Reviewer Kai の「公式アウトプット」として扱う。
- Human（啓＋ChatGPT）は：
  - doc_update_proposal_v1＋doc_update_review_v1 を読み、
  - proposal 全体を **ACCEPT** するか **REJECT** するかを決める。
- Phase 2 の間は、**proposal 全体の採用/不採用** を扱い、
  updates 単位の部分適用は後続フェーズの課題とする。
- JSON の中身を人間が直接編集することは避け、
  必要な補足や異論は外側（レポート、Issue コメント等）に記録する。
