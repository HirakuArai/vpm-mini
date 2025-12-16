# hakone-e2: SSOT分離（Project黒板 vs Domain事実ストア）v1

## 目的
hakone-e2 は「箱根駅伝の事実を情報化してE²的に扱えるようにする」プロジェクト。
このとき、プロジェクト運用の情報と、箱根駅伝の事実データは混ぜない。

## Project SSOT（黒板）
- data/hakone-e2/info_nodes_v1.json
- data/hakone-e2/info_relations_v1.json
役割:
- 決定 / タスク / gap / 運用ルール / 設計 / 進捗 / 証跡

禁止:
- 箱根駅伝の事実（年/区間/結果など）を canonical fact としてここに入れない

## Domain SSOT（箱根駅伝の事実・根拠）
- data/hakone-e2/domain/ 配下で管理（別スキーマ）
役割:
- scene / claim（断定）/ evidence（根拠）/ hypothesis（仮説）を扱う
- claim は必ず evidence を参照する（推測で断定しない）

## 運用
- 「どう進めるか」は Project SSOT
- 「何が起きたか（事実）」は Domain SSOT
- docs/projects/hakone-e2/scenes/* は “仕様/テンプレ/作業メモ” としてはOKだが、
  断定的事実は domain の claim/evidence に落とす。
