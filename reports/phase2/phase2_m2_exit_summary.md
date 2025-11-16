# Phase 2 / M2 Exit Summary

context_header: repo=vpm-mini / branch=main / phase=Phase 2 後半

本レポートは、Phase 2 後半（M2: ルール運用 → 半自動）で確立したセル運用の成果を、Hello S5 / u_contract / metrics-echo / PR Groomer の 4 つの観点から短くまとめたものである。詳細な事実・ログは `STATE/current_state.md` および `docs/memory/**` を参照。

---

## 1. Phase 2 後半（M2）の目的

- /ask + Codex + 人間 + u_contract による「自己更新ループ」を、少数セルで実際に回し、その事実を SSOT に刻む。
- 特に:
  - Hello S5 を模範ケースとした North Star 更新ループ
  - u_contract による persist-report 半自動レーン
  - metrics-echo の「plan-only /ask」という棚上げパターン
  - PR Groomer による役割分類の最低限ライン
  を確認する。

---

## 2. Hello S5 /ask update_north_star ループ（模範セル）

- Codex が Hello S5 直近 run から CONTEXT_JSON を構成。
- `/ask update_north_star` を実行し、LLM から `state_patch` / `memory_patch` を JSON で取得。
- 啓さんが採用範囲を判断し、Codex が PR #754 で:
  - `STATE/current_state.md`
  - `data/vpm_memory_min.json`
    を更新。
- `docs/memory/egspace_m2_insights.md` と `STATE/current_state.md` の「Phase 2 / M2 snapshot (North Star & u_contract)」に、このループを Phase 2 / M2 の模範ケースとして記録。

→ 結果として、**「/ask → patch → 人間判断 → PR → STATE/メモリ/EG-Space 同期」** という、模範セルの自己更新ループが 1 つ完成した。

---

## 3. u_contract `persist-report` レーン（半自動運用）

- PR #757 で `docs/memory/u_contract_policy.md` v1 を作成。
  - カテゴリ: `persist-report` / `sample-candidate` / `sample-archive` / `stale-or-obsolete`
  - 各カテゴリごとの default action（auto-merge 候補 / レビュー必須 / close 候補）を定義。
- Codex が open PR から `persist-report` を検出し、#742 / #737 / #684 に `u_contract:persist-report` ラベル＋コメントを付与。
- 啓さんが diff と CI を確認し、3本ともマージ。
- `docs/memory/egspace_m2_insights.md`（PR #763）と `STATE/current_state.md`（PR #766）に、`reports/**` のみ変更＋CI Green なら M2 では Codex 整理 → 人間 1クリックマージで回せる半自動レーンとして明記。

→ `persist-report` については、**「エージェントが整理し、人間は 1 クリックマージで流すレーン」**が Phase 2 / M2 で確認できた。

---

## 4. PR Groomer：最小 CONTEXT での役割分類

- `/ask pr_groomer_suggest` に対して #731 / #723 の CONTEXT_JSON を投入。
  - #731 → persist-report / auto-merge 候補
  - #723 → sample-candidate / レビュー必須
- フル PR 情報がなくても、「レポート系かサンプル系か」の座標を置けることを確認。

→ /ask に必要な CONTEXT の「最低限解像度ライン」を把握し、**「完全なメタ情報がなくても、役割分類だけなら十分に可能」**という前提が置けた。

---

## 5. metrics-echo /ask（plan-only ケース）と宿題化

- `infra/k8s/overlays/dev/metrics-echo-ksvc.yaml` と手動 ready-check テキストを Evidence として Issue #764 から `/ask update_north_star` を実行。
- ask-entry run は success だが、`state_patch` / `memory_patch` は返らず、plan / warnings のみ（plan-only）。
- `STATE/current_state.md` の M2 snapshot で、「現状の Evidence では North Star に固定せず、監視設計と Evidence 形式を整理してから後続フェーズで再チャレンジする」という方針を明記。
- PR #769 で `docs/memory/metrics_echo_design.md` を作成し、Phase 3 以降の監視/Evidence 設計メモとして位置づけ。`docs/memory/egspace_m2_insights.md` からもリンク。

→ Phase 2 / M2 では、**「/ask を回しても patch なし（No-op）なゴール」**のパターンを一度踏み、無理に North Star を書き換えず **「宿題セル」として扱うルール**を取り込んだ。

---

## 6. Execution Policy と Phase 3 への橋渡し

- PR #767 で `docs/overview/phase3_skeleton.md` に Execution Policy を追加。
  - 標準ルート: 仕様 → エージェント実行 → PR → 人間レビュー
  - 例外ルート: 緊急 Hotfix（人間直接編集、理由と diff を後追い記録）
  - レビューの役割: 人間は意味・整合性・リスクに集中
  - 権限境界: 将来的に VM Codex / LLMリレーなど限定された実行環境へ集約
- PR #768 で `STATE/current_state.md` の `## Phase 3 (draft)` に、実行主体のエージェント化（ローカル Mac Codex → エージェントレーン）を δ として明文化。

→ Phase 2 / M2 の出口時点で、**「Phase 3 ではセルを増やすだけでなく、実行主体もエージェント側へ移行していく」**という方針が SSOT に反映された。

---

## 7. Phase 2 / M2 のまとめ

- Hello S5 を通じて、模範セルの自己更新ループが 1 つ完成した。
- u_contract `persist-report` レーンで、reports/** 限定 + CI Green の半自動運用が確認できた。
- PR Groomer により、最小限の CONTEXT で PR の役割分類が可能であることを確認した。
- metrics-echo は /ask plan-only の結果を受けて、監視/Evidence ライン設計の宿題セルとして整理された。
- Execution Policy と Phase 3 (draft) により、Phase 3 では「セル増殖」と「エージェント主導の実行」に軸足を移す方針が定義された。

→ Phase 2 / M2 の目的である **「少数セルで /ask＋Codex＋人間による自己更新ループを実際に回し、その事実とルールを SSOT に刻む」** は達成されたとみなせる。
