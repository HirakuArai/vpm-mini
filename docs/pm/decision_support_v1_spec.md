# decision_support_v1_spec

## 1. 目的と位置づけ

`decision_support_v1` は、VPM（Kai & Friends）における

> プロジェクトについて「何をどう決めるか」を支援するレーン

の仕様である。

このレーンは、啓（人間）や外部ツールからの「判断してほしい／整理してほしい」という依頼を受けて、次を行う。

- 論点（問い）を整理し直す
- 選択肢（options）を構造化して提示する
- 現時点での暫定的な推奨案（recommended_option）と理由（rationale）を出す
- 必要に応じて、Doc Update レーン（P3）への橋渡しを提案する

最終的な決定は人間が行うが、`decision_support_v1` はそのための **事前整理と意思決定支援** に専念する。

---

## 2. 他レーンとの関係（P1 / P2 / P3）

VPM が「管理に専念」するときの内部処理は、次の 3 パターンに整理する。

- P1: `ask_pm_v1`（状況を知る／理解する）
  - 入力: 質問（自然文）
  - 出力: 回答＋必要に応じて根拠（どの STATE / reports / docs を見たか）
- P2: `decision_support_v1`（何をどう決めるかを支援する）← 本ドキュメント
  - 入力: 論点・問い
  - 出力: 選択肢＋暫定的な推奨案＋理由＋次ステップ案
- P3: `doc_update_pm_v1`（現実や決定を SSOT に反映する）
  - 入力: progress_summary（何が起きたか・何を反映したいか）
  - 出力: doc_update_proposal_v1（Aya 用）

典型的な組み合わせは次の通り。

- 「議論する」
  - P1（状況整理）＋ P2（方針案を出す）
- 「結論を出す」
  - P2（方針を絞る）＋ P3（決定内容を SSOT に記録する）

`decision_support_v1` はこのうち **P2** にあたる。

---

## 3. 入力スキーマ（Input Schema）

### 3.1 JSON 例（イメージ）

    {
      "project_id": "vpm-mini",
      "topic": "Phase 2 のゴール設定",
      "question": "Phase 2 の終了条件をどこに置くべきか？",
      "context_refs": [
        "STATE/vpm-mini/current_state.md",
        "docs/projects/vpm-mini/project_definition.md"
      ],
      "constraints": {
        "deadline": "2025-12-31",
        "priorities": ["コスト抑制", "Kaiの自律性PoC"],
        "hard_limits": ["GKE 月額コストは X 円以下"]
      },
      "mode": "explore",
      "history": [
        {
          "type": "discussion_summary_v1",
          "ref": "reports/vpm-mini/2025-11-30_weekly.md#phase2-discussion"
        }
      ],
      "caller": {
        "role": "human",
        "name": "啓",
        "intention": "Phase 2 をどこで区切るかを現実的に決めたい"
      }
    }

### 3.2 フィールド定義

- project_id (string, required)  
  対象プロジェクト ID。例: "vpm-mini"。

- topic (string, required)  
  論点のラベル。1〜2 行程度。

- question (string, required)  
  「何を決めたいのか」を表す自然文の問い。

- context_refs (string[], optional)  
  参照すべき SSOT ドキュメントのパス。  
  例: "STATE/...", "docs/projects/...", "reports/..."。

- constraints (object, optional)  
  意思決定時に考慮すべき制約条件。
  - deadline: 日付文字列
  - priorities: 優先する軸のリスト（例: コスト、速度、安全性）
  - hard_limits: 絶対に破れない制約（例: コスト上限、法的制約）

- mode (string, optional, default: "explore")  
  - "explore": 選択肢を広く出すモード
  - "converge": 既に候補が絞られており、結論に近づきたいモード

- history (array, optional)  
  過去の議論や関連決定への参照（discussion_summary_v1 など）。

- caller (object, optional)  
  呼び出し元に関する簡単な情報（人間／別レーンなど）。

---

## 4. 出力スキーマ（Output Schema）

### 4.1 JSON 例（イメージ）

    {
      "decision_support_v1": {
        "normalized_question": "Phase 2 の終了条件をどこに置くかを決める",
        "context_used": [
          "STATE/vpm-mini/current_state.md#phase2-goal",
          "docs/projects/vpm-mini/project_definition.md#phase2"
        ],
        "assumptions": [
          "Phase 2 の主目的は『kind+Knative 足場づくり』である",
          "Phase 3 以降で Swarm 拡張を扱う予定である"
        ],
        "options": [
          {
            "id": "A",
            "title": "Hello KService READY=True を Phase 2 の DoD とする",
            "description": "kind+Knative 足場構築と Hello KService READY=True までを Phase 2 の完了条件とする。",
            "pros": [
              "短期ゴールが明確になり集中しやすい",
              "Phase 2 を『足場づくり』に限定できる"
            ],
            "cons": [
              "Phase 3 初期に追加タスクが膨らむ可能性がある"
            ],
            "risks": [
              "Hello 以外のサービス移植が遅れた場合、Swarm PoC が後ろ倒しになる"
            ],
            "likely_impacts": [
              "短期: 開発負荷が下がる",
              "中期: Phase 3 の計画調整が必要になる"
            ]
          },
          {
            "id": "B",
            "title": "Hello + 1 サービス移植までを Phase 2 の DoD とする",
            "description": "Hello KService に加えて、Compose サービスのうち 1 つを Knative Service として移植する。",
            "pros": ["Swarm PoC までの距離が縮まる など"],
            "cons": ["作業量が増える など"],
            "risks": [],
            "likely_impacts": []
          }
        ],
        "recommended_option": "A",
        "rationale": "Phase 2 の役割を『足場づくり』に限定したいという現状方針と整合的であり、現実的な負荷とスケジュール感のバランスが良いため。",
        "open_questions": [
          "Phase 3 の開始条件をどこまで明文化するか？",
          "Hello 以外のサービスの優先順位をどう決めるか？"
        ],
        "suggested_next_flows": [
          {
            "type": "P3_doc_update",
            "when": "recommended_option が人間により承認された場合",
            "targets": [
              "STATE/vpm-mini/current_state.md",
              "docs/projects/vpm-mini/project_definition.md"
            ],
            "note": "Phase 2 のゴール定義を更新し、Phase 3 の入口条件も追記する。"
          }
        ],
        "meta": {
          "generated_at": "2025-11-29T06:30:00+09:00",
          "generator": "Kai PM (ChatGPT)",
          "confidence": "medium"
        }
      }
    }

### 4.2 フィールド定義（主要項目）

- decision_support_v1 (object, required)  
  レーンのトップレベルオブジェクト。

- normalized_question (string, required)  
  入力 question を「何を決めるべきか」という形に正規化したもの。

- context_used (string[], optional)  
  実際に意思決定の材料として参照した SSOT のパス。

- assumptions (string[], optional)  
  推論や提案の前提となっている仮定・前提条件。

- options (array, required, length >= 2 推奨)  
  各選択肢を表すオブジェクトの配列。  
  各要素は少なくとも以下を含む。
  - id (string)
  - title (string)
  - description (string)
  - pros (string[])
  - cons (string[])
  - risks (string[])
  - likely_impacts (string[])

- recommended_option (string, optional)  
  暫定的に推奨する選択肢の id。  
  推奨を出さない場合は省略し、その理由を rationale に記載する。

- rationale (string, optional)  
  recommended_option に至った理由、または「推奨を出さない」理由。

- open_questions (string[], optional)  
  まだ決まっていない論点や、追加で検討が必要な問い。

- suggested_next_flows (array, optional)  
  次に起動が望ましいレーンの提案。  
  例: type: "P3_doc_update" など。

- meta (object, optional)  
  生成メタ情報（生成時刻、生成者、confidence など）。

---

## 5. 振る舞いガイドライン（プロとしてのチェックリスト）

`decision_support_v1` を生成するロール（Kai / 将来の Hana 経由など）は、次の原則に従う。

### 5.1 やるべきこと

1. 問いを正規化する  
   - 入力 question がぼんやりしていても、  
     「これは結局、〇〇について △△ を決める問いだ」  
     という形に normalized_question を整理する。

2. SSOT に基づいて考える  
   - 可能な限り STATE / docs/projects / reports などを前提にする。
   - SSOT に存在しない前提は assumptions に明示する。

3. 選択肢を構造化する  
   - 原則として 2 つ以上の option を出す。  
   - 各 option について Pros / Cons / Risks / Impacts をバランスよく書く。

4. おすすめは「暫定案」として出す  
   - recommended_option はあくまで暫定的な推奨案。  
   - 人間の価値判断が強く関わる場合は、その旨を rationale で明記する。

5. 次にやるべきことを提案する  
   - 決定が SSOT に反映されるべき場合、  
     suggested_next_flows に P3（doc_update_pm_v1）起動の提案を書く。

### 5.2 やらないこと・注意点

- 最終決定を勝手に「確定」と書かない  
  - 常に「暫定案」または「候補」として扱う。

- SSOT と矛盾する前提を暗黙に置かない  
  - 矛盾がある場合は、それを指摘し、assumptions か open_questions に明示する。

- 人間の価値観を断定しない  
  - 「啓さんは〜を重視するはず」などの断定は避け、  
    どの価値観の違いが選択に影響するかを構造として説明する。

---

## 6. 代表的ユースケース

1. Phase 2 の終了条件を決める  
   - topic: "Phase 2 ゴール"  
   - question: "Phase 2 をどこで区切るべきか？"

2. GKE コスト削減方針のレベル感を決める  
   - topic: "GKE コスト削減"  
   - question: "どこまで削るべきか？"

3. Hana の実装スコープを決める  
   - topic: "Hana 仕様"  
   - question: "Phase 2 で Hana をどこまで実装するか？"

---

## 7. 今後の拡張と自律化との関係

将来的には、次のような連携を想定する。

- decision_support_v1 → decision_record_v1（人間が選んだ option）→ P3 (doc_update_pm_v1)

Phase 2 の段階では、

- decision_support_v1 は ChatGPT（Kai PM）が返す JSON 構造として運用し、
- 啓がその内容をレビューして選択肢を採用する／修正する。

実運用を通じて、本 spec（decision_support_v1_spec）は随時アップデートしていく。
