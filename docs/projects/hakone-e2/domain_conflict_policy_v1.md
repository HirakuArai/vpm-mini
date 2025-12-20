# Domain Lane Conflict Policy v1 (hakone-e2)

目的：Fact Lane（facts抽出）で発生する「矛盾（conflict）」を、毎回同じ手順で検知・レビューできるようにする。
ここでの矛盾は「同一 claim.key に対して value が一致しない」状態を指す。

## 1) 基本原則
- claim.key は「同一断定=同一キー」。key が同一で value が異なれば conflict として扱う。
- conflict の解決は v1 では自動化しない（レビュー必須）。ただし “推奨” は提示してよい。
- evidence（根拠）は必須。矛盾解決は evidence の強さ（優先度）に依存する。

## 2) 優先ソース順（推奨）
以下の順で “採用候補（recommended）” を決める。
1. official（主催/公式リザルト/公式PDF等）
2. semi_official（放送公式・大会公式ページなど）
3. media（大手報道）
4. other

※ evidence.type を使って機械的に判定し、facts lane は推奨を `conflicts_summary.md` に出力する。

## 3) レビュー手順（PRレビューでやること）
- `conflicts.json` と `conflicts_summary.md` を見る
- 各 conflict key について：
  - 根拠（evidence_refs）の種類（official/media等）を確認
  - 推奨が妥当ならそのまま採用（追加の調査が必要なら TODO として残す）
- v1 では “採用版/保留版” のSSOT上の表現（status等）は導入しない（将来拡張）

## 4) 出力（facts laneのartifact）
- `conflicts.json`：機械判定の素材（keyごとの候補）
- `conflicts_summary.md`：人間向け要約（推奨を含む）
