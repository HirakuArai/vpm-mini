# info_update_plan v1（info_network 更新計画）

## 目的
canonical info_network（data/**/info_nodes_v1.json と info_relations_v1.json）と、新規 snapshot_raw（bundleから生成された info_nodes/info_relations）を統合する際の「更新計画」を表現する。

update_plan は「何を add / update / obsolete / supersede するか」を明示し、apply処理は判断せず命令書どおりに反映する。

## 想定フロー上の位置づけ
1) 新しい情報 → info_source_bundle_v1  
2) bundle → snapshot_raw（info_nodes/info_relations）  
3) canonical + snapshot_raw → update_plan（意味付き調停）  
4) canonical + update_plan → canonical'（機械適用）

## スキーマ（v1.1）
- project_id: string
- source_snapshot_id: string（任意の識別子）
- generated_at: string（ISO 8601推奨）
- matches: [{"new": "<new_id>", "existing": ["<old_id>", ...]}]
- add: info_node_v1[]
- update: info_node_v1[]
- obsolete: string[]（node id）
- add_relations: info_relation_v1[]
- update_relations: info_relation_v1[]
- obsolete_relations: string[]（relation id）
- supersedes: [{"new": "<new_id>", "old": ["<old_id>", ...]}]
- notes: string

## フィールドの意図（要点）
- matches: 対応付け（1対多/多対1を含む）を表す材料。applyは参照せず、判断者（AI/人）が使う。
- add/update/obsolete: ノード操作
- add_relations/update_relations/obsolete_relations: リレーション操作
- supersedes: new が old 群を置き換える（統合/方針転換）関係。applyは決定的に supersedes relation を生成して追加する。
