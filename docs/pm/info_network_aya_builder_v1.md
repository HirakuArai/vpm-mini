# Aya: info_network_builder_v1

## 1. 目的

Aya: info_network_builder_v1 は、人間や Codex が集めた「素材テキスト」から、info_network_overview_v1 で定義された info_node と info_relation を生成する役割を担う。

v1 では、特に以下を対象とする。

- project_id が "vpm-mini" のプロジェクト
- scope が "phase2-p2-2-hello" の範囲
- つまり、Phase 2 の中でも「P2-2: Hello KService READY=True」に関する情報を info_network に載せることに集中する

将来的には、他の scope や他プロジェクトにも拡張するが、v1 では上記にフォーカスする。

---

## 2. Aya が使う前提知識

Aya は、info_network に関する以下のドキュメントを前提知識として持つ。

- docs/pm/info_network_overview_v1.md
  - info_node のフィールド、kind の種類、ルール
  - info_relation のフィールド、type の種類、ルール
  - project_id / phase / lane / scope / tags による「所属」の扱い
- 既存の seed の例
  - data/info_network_v1/phase2_p2-2_hello_seed.yml

Aya はこれらの内容を理解しているものとして、info_node と info_relation を生成する。

---

## 3. 入力（Aya が読むもの）

Aya は、黒板やプロンプト経由で与えられた「素材テキスト」から変換を行う。

素材テキストの例:

- STATE/current_state.md の抜粋
- reports 以下のレポートの抜粋
- P2-2: Hello KService に関する GitHub Issue や PR の本文
- devbox や kind + Knative に関するコマンドログ
- 人間が書いたメモや設計ノート

v1 では、

- 素材は人間や Codex が手動で選び、Aya に渡す
- Aya は、その素材だけを前提に info_node / info_relation を提案する

という前提でよい。素材の自動収集は v1 のスコープ外とする。

---

## 4. 出力（Aya が返すもの）

Aya は、与えられた素材テキストから、

- info_node のリスト
- info_relation のリスト

を YAML 形式で返す。

基本フォーマット:

- 既存ファイルに append するか、新しいファイルを作るかは、呼び出し側で決める
- Aya 自身は「YAML の中身」を返すことに集中する

例（v1 のイメージ）:

project_id: "vpm-mini"
scope: "phase2-p2-2-hello"

nodes:
  - id: "P2-2-EXPECTED-READY-001"
    subject: "p2-2-hello-ksvc@dev"
    kind: "expected_state"
    statement: "dev環境で kubectl get ksvc hello が READY=True を安定して返す。"
    phase: "phase2"
    lane: "infra"
    scope: "phase2-p2-2-hello"
    status: "active"
    author: "aya"
    created_at: "2025-12-06T12:00:00+09:00"
    evidence_refs: []
    tags: ["phase2", "p2-2", "expected", "hello-ksvc"]

relations:
  - id: "REL-P2-2-EXPECTED-REFINES-P2-2-GOAL"
    type: "refines"
    from: "P2-2-EXPECTED-READY-001"
    to: "P2-2-GOAL-001"
    note: "P2-2 のゴールを具体的な期待状態に落とし込んだ。"

呼び出し側は、この出力を data/info_network_v1/ 以下の適切なファイルに保存する。

---

## 5. ルール（info_node 生成時の注意）

Aya が info_node を生成する際は、info_network_overview_v1 のルールに従う。

特に:

1. 1ノード = 1 subject × 1 kind × 1文

   - statement は、そのノードだけを読んでも意味がわかる 1 文にする
   - 対象や前提をいくつも詰め込みすぎない
   - 分割できる場合は、別ノードとして分ける

2. 所属フィールドの扱い

   - project_id は v1 では "vpm-mini"
   - phase は可能なら "phase2" を付ける
   - lane は、素材の内容に応じて "infra" や "pm" などを推定する
   - scope は "phase2-p2-2-hello" を基本とし、必要ならより細かい scope 名の案をコメントとして補足する
   - tags は、後から人間がフィルタしやすいよう、phase / scope / kind / subject に対応するキーワードを付ける

3. kind の選択

   - 目的に関する文は purpose
   - こうなっていてほしい条件は expected_state
   - コマンド結果や現状報告は actual_state
   - やってはいけない条件や枠は constraint
   - 「こうだと仮定している」は assumption
   - 明示的に「こうする／こうしない」と決めたことは decision

4. ID の扱い

   - 既存の seed (phase2_p2-2_hello_seed.yml) にある ID は尊重する
   - 新しいノードには、新しい ID を提案する
   - ID の形式は "P2-2-種別-連番" のように、人間が見てもおおよそ推測できる形を目安とする

---

## 6. ルール（info_relation 生成時の注意）

info_relation についても、info_network_overview_v1 のルールに従う。

特に:

1. type の選択

   - refines:
     - 上位の目的や期待を、より具体的な目的や期待に分解するとき
   - supports:
     - 上位の目的や期待を、間接的に後押しする要素のとき
   - blocks:
     - そのノードの内容が満たされない限り、上位の期待が達成されないとき
   - depends_on:
     - 実務上の順序や依存関係を表すとき

2. グラフ構造

   - 可能な限り、循環しない構造になるようにする
   - 「A が B を支える」関係と「B が A を支える」関係を同時に作らないように注意する

3. note の利用

   - なぜその relation を張ったのかが一目でわかるよう、note に短い説明を書く
   - 必要であれば、日本語で簡潔に補足する

---

## 7. v1 のスコープ

info_network_builder_v1 としての Aya の責務は、v1 では次の範囲に絞る。

- プロジェクト:
  - project_id が "vpm-mini" のみ
- スコープ:
  - scope が "phase2-p2-2-hello" の範囲
- 入力:
  - 人間や Codex が選んだ素材テキスト（STATE / reports / issue / ログなど）
- 出力:
  - info_node および info_relation の YAML 断片
- 未対応:
  - ログの自動クロール
  - 他プロジェクトや他 scope の info_network 化

Aya は、この限定されたスコープの中で、安定して「素材 → info_network YAML」変換を行えるようになることを v1 のゴールとする。
