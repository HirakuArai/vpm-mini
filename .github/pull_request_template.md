## 概要
<!-- 変更の要点を1-3行で -->

## 変更ファイル  
<!-- 主にどの領域か: code/docs/reports/workflows ... -->

## DoD（共通／必須）
> **参照**: `.ops/dod/policy.yml` - 全PR必須遵守項目

### ✅ 必須チェック項目
- [ ] **Auto-merge (squash) 有効化**
- [ ] **CI 必須チェック Green**（test-and-artifacts, healthcheck）  
- [ ] **merged == true を API で確認**
- [ ] **PR に最終コメント**（✅ merged / commit hash / CI run URL / evidence）
- [ ] **必要な証跡（例: reports/*）を更新**

### 🚧 Gate確認
- [ ] **G0**: 開始宣言＆承認待ち（該当する場合）
- [ ] **G1**: .github/workflows/** 変更時は承認必須（該当する場合）
- [ ] **G2**: 競合解決完了（該当する場合）  
- [ ] **G3**: Verify成功確認（該当する場合）
- [ ] **G4**: 最終サマリ→承認確認（該当する場合）

## 証跡・Evidence
- CI Run: <!-- 後で更新 -->
- Evidence File: <!-- reports/* 等 -->
- Final Comment: <!-- PRに投稿する最終コメントのURL -->

---
**⚠️ 重要**: このPRはmerged状態確認＋最終コメント投稿まで責任を持って完遂すること
