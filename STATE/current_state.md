```yaml
# === State Declaration (Single Source of Truth) ===
active_repo: vpm-mini
active_branch: main
phase: Phase 0 Complete   # Step 1-10 all done; Step 10 declared
context_header: "repo=vpm-mini / branch=main / phase=Phase 0 Complete"
short_goal: "Phase 1 preparation: KPI design & PoC architecture"
exit_criteria:
  - "✅ Phase 0 Complete: Step 1-9 done; Step 10 declared"
  - "✅ docs/PHASE0_COMPLETION.md: Evidence collection and next phase roadmap"
  - "✅ Phase0-Health CI: Single required check with auto-artifacts"
  - "✅ Auto-PR/Auto-merge: feat/* → main workflow fully operational"
next_goals:
  - "Phase 1 - KPI design & PoC infrastructure"
  - "Multi-agent coordination architecture"
  - "Vector DB integration planning"
updated_at: 2025-08-19T18:00+09:00
# リポ切替時は必ず PR を作成し、タイトルに 'Decision: switch active_repo to …' を含めること
```

# この文書の役割

本プロジェクトでは、事象目的空間における **現在地（C）**、**ゴール（G）**、およびその差分ベクトル **δ（方向と距離）** を常に把握し、そこから導かれる**次の行動方向**を明確にすることを重視している。

この圧縮サマリーは、そのために必要な**最新の事実・決定・課題**を短く構造化し、新しいセッション開始時に読み込むことで、経緯や雑談を違らずに即座に同じ認識から会話を再開することを目的とする。

---

## プロジェクトの最終目的

**Hyper-Swarm / VPM** を構築し、複数のAIエージェントの連携による**常時自己進化型の開発運用基盤**を確立する。

これにより、コード実装・レビュー・修正・ドキュメント更新を**自徴サイクル**で回し、進捗と成果を可視化しながら安全に拡張可能なアーキテクチャを実現する。

---

## フェーズ構成と位置づけ

1. **Step-A** – 基盤機能実装（チャットUI、ログ、要約Pipeline、品質ガード）
2. **Phase 0** – 5 Roles スケルトン試走
3. **Phase 1** – PoC 実\u8証 + KPI可視化
4. **Phase 2** – 小規模Swarm + Vector DB連携
5. **Phase 3** – EG-Space完成 & セキュア化

**現在地:** Step-A-2（P0の完了が直近ゴール）
**ゴール（短期）:** P0全タスク緑化 → Phase 0 移行

---

## 現在地（C）

* Mermaid 図管理方式を確立（`.md` + コードフェンス形式）
* Node.js 20 & Mermaid CLI 最新化済み
* `scripts/export_diagrams.sh` で `diagrams/src/*.md` → `.svg` 一括変換可能
* GitHubリポジトリに図のソース（.md）を保存、SVGは必要時のみ生成
* エージェント / Codex / Claude Code の役割分担方針確立

---

## ゴール（G）

* **短期（P0完了）:**

  * 要約Pipeline実装 (`summary.py`) ＋ ユニットテスト緑化
  * README拡充（10分再現チュートリアル＋セットアップ手順）
* **中期（Phase 0完了）:**

  * 5 Roles の試走環境構築とセル間連携のPoC
* **長期:**

  * フルEG-Space連携＋常時自己進化サイクルの安定運用

---

## 差分（δ：方向と距離）

* **距離:** P0完了まで残りタスク 2件（P0-2, P0-3）
* **方向:** 要約Pipeline → README拡充 → Phase 0準備

---

## 優先タスク

**P0-2:** 要約Pipeline実装

* `summary.py` に最新1000token要約生成 → `memory.json` 先頭追記
* テスト (`tests/test_summary.py`) で要約長 ≤400字確認

**P0-3:** README拡充

* 10分再現チュートリアル
* セットアップ手順（Node.js 20 / Mermaid CLI / VS Code プレビュー）

---

## 制約条件・決定事項

* 図は `.md` 形式（コードフェンス付き）で `diagrams/src/` に保存
* 画像生成は `scripts/export_diagrams.sh` 実行時のみ
* GitHubには `.md` をソースとして管理（SVGは必要時のみ）
* Node.js は v20系固定
* Mermaid CLI 最新版使用

---

## 未確定 / 保留

* Phase 1以降のKPI項目詳細
* 本番運用でのSecrets管理仕様（BOTトークンの権限分離方針は確立済みだが実装未着手）

---

**使い方の要点**

* 迷ったらこの文書冒頭の **宣言ブロック** を見る（唯一の前提）。
* 依頼やPRは **コンテキスト・ヘッダ** から始める。
* 進捗は **チェックリスト** で機械的に判定する。
