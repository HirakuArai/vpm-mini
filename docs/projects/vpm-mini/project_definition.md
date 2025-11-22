# プロジェクト定義: vpm-mini

## 1. プロジェクト名
vpm-mini（Virtual Project Manager / Hyper-Swarm ミニ版）

## 2. 目的（Purpose）

- GitHub と LLM を中核として、
  **AI がプロジェクトマネージャー（PM）として機能するための最小構成 VPM** を作る。
- 「情報収集・蓄積・考察・提案」を、状況変化に追従しながら継続的に回せることを証明する。
- 将来、他プロジェクト（例：箱根E² や 会社業務プロジェクト）にも横展開可能な「PMエンジン」を確立する。

## 3. スコープ（Scope）

- 対象:
  - vpm-mini リポジトリ内のコード・ドキュメント・GitHub Issues / PR / Actions。
- 含めるもの:
  - PM Kai v1（C/G/δ + Next 3 を一貫して出せる状態）の構築。
  - STATE / reports / project_definition の整備。
- 含めないもの（現フェーズでは扱わない）:
  - VM / GKE 上での自律実行。
  - 5セルの物理分散。
  - Kai 自身が自動で commit / deploy する自律進化。

## 4. 成功条件（Success Criteria）

- いつでも Kai に以下を聞いて、破綻なく答えが返ってくる:
  - 「このプロジェクトの目的は？」
  - 「いまの C/G/δ は？」
  - 「Next 3 と、その理由を教えて。」
- それらの答えが、`STATE/vpm-mini/current_state.md` と
  `reports/vpm-mini/*.md` と矛盾しない。
- 最低 2〜3週間、週次で PM Kai を使いながら、
  「人間の感覚から見ても妥当な提案が出ている」と判断できる。

## 5. 制約（Constraints）

- 実行環境は Mac + GitHub + LLM API に限定する。
- 破壊的な操作（クラスタ削除、インフラ変更など）は PM ゴールから除外する。
- PM Kai は「提案」までを行い、「最終判断と実行」は人間が行う。

## 6. フェーズ（現時点のフォーカス）

- 現在地: Phase 2 = 「PM Kai v1（GitHub + LLM）を成立させる」フェーズ
- 次フェーズ候補:
  - 他プロジェクトへの展開（project_id 切り替え）
  - EG-Space / 5セルの“論理実装”
  - その後に、自律実行（VM/GKE）フェーズ
