# Gen PM Snapshot date spec v1 (vpm-mini)

context_header: repo=vpm-mini / branch=main / phase=Phase 2 (Gen / PM Snapshot date spec v1)

この文書は、Gen が生成する PM Snapshot において「どの日付のスナップショットを出すか」を明確にし、「最新ではなく前日が出る」ような曖昧挙動を仕様レベルで禁止する。範囲指定（直近 n 日など）は v1 スコープ外とし、別能力で扱う。

## 1. 基本方針（v1）
- PM Snapshot の単位は「1日分のスナップショット」に限定する（例: 2025-11-30 時点の C / G / δ / Next）。
- Gen は必ずターゲット日付を明示的に受け取る。フィールド名は as_of_date（文字列）、形式は YYYY-MM-DD（例: 2025-11-30）。
- Gen は as_of_date 以外の日付を勝手に選ばない。「最新」「昨日」「最後に更新された日」のような推測ロジックは禁止。
- タイムゾーン基準は Asia/Tokyo（JST）。as_of_date は JST で解釈し、UTC を内部で扱う場合も「JST での当日」とずれないようにする。

## 2. 入力仕様（Gen が受け取るべきもの）
- 共通フィールド
  - project_id: v1 では "vpm-mini"
  - as_of_date: YYYY-MM-DD 形式（必須）
  - mode: v1 では "daily_snapshot" 固定（将来拡張用）
- as_of_date の扱い
  - 必須入力とし、省略可にしない。
  - デフォルトが必要なら Workflow 側で「今日の JST 日付」を計算して渡す。
  - Gen 実装は as_of_date 未指定を想定せず、未指定はバグ扱い。

## 3. 出力仕様（Gen が作るもの）
- レポートファイル
  - パス例: reports/vpm-mini/2025-11-30_vpm-mini.md
  - ファイル名は as_of_date と project_id の組み合わせを基本とする。
- レポートの意味
  - 「as_of_date 時点の PM Snapshot」であることを明示し、中身は既存の PM Snapshot 仕様（C / G / δ / Next）を踏襲。
- 禁止事項
  - 「レポートディレクトリから最新のファイルを探して返す」ロジックは禁止。
  - 必ず as_of_date に従い、その日付のレポートを生成または参照する。

## 4. 「前日が出てしまった」問題の扱い（アンチパターン）
- 過去に「最新を期待したのに前日分が出た」事例があったことを記録。
- 想定原因
  - as_of_date の指定がなかった。
  - Gen 実装が「最新っぽいファイル」や「昨日」のような heuristics で選んでいた。
- v1 の方針
  - as_of_date を必須にし、Gen が内部で日付を推測しない。
  - これにより「昨日になってしまう」「理由が不明」といった挙動を仕様レベルで禁止する。

## 5. 将来拡張（what_changed 系能力との分離）
- 「何日分」「直近7日間で何が起こったか」という問いは PM Snapshot とは別能力（例: Kai-0 what_changed_v1）で扱う。
- PM Snapshot（Gen）は「ある1日（as_of_date）のスナップショット」に集中する。
- 将来、期間集計を Gen が担う場合は、別 mode（例: range_summary）として定義し、別 spec や別レーンで扱う。

## 6. Workflow / 黒板との関係（方向性）
- pm_snapshot.yml
  - workflow_dispatch inputs に as_of_date を追加する方向で検討。
  - 指定がない場合も Workflow 内で「今日の JST 日付」を計算して明示的に渡す。
- 黒板（将来）
  - pm_snapshot_request_v1 を定義する場合、payload に as_of_date を必須フィールドとして含める。
  - Gen は黒板 entry の as_of_date に従い、他の日付の snapshot を作らない。
- 本 spec は「日付まわりのルール」に限定し、黒板全体の設計は別ドキュメントで扱う。
