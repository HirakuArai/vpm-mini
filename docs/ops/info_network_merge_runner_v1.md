# info_network merge runner v1

目的：bundle を入力に、info_network の update cycle（既存＋新規マージ）を高速に回す。

## 使い方

dry-run（suggestionだけ作る）:
```bash
scripts/info_network/merge_run_v1.sh --project-id hakone-e2 --bundle <bundle.yaml> --mode dry-run
```

apply（questions=0 のときだけ apply して止まる）:
```bash
scripts/info_network/merge_run_v1.sh --project-id hakone-e2 --bundle <bundle.yaml> --mode apply
```

pr（apply → commit → push → PR作成）:
```bash
export PR_BOT_TOKEN=...   # 推奨（required checks を確実に回す）
scripts/info_network/merge_run_v1.sh --project-id hakone-e2 --bundle <bundle.yaml> --mode pr
```

## ポリシー

additive only（supersedes/obsolete を強制的に空にする）:
```bash
scripts/info_network/merge_run_v1.sh --project-id hakone-e2 --bundle <bundle.yaml> --mode pr --policy additive_only
```

重複drop（id部分一致 / regex）:
```bash
scripts/info_network/merge_run_v1.sh --project-id hakone-e2 --bundle <bundle.yaml> --mode pr \
  --drop-add-id-contains evidence_gap_dod \
  --drop-add-id-regex hakone-e2:decision:ops-v1-fix-v1
```

## env
`.env` が repo root に無ければ `--env /path/to/.env` を使う（fallback: /Users/hiraku/projects/vpm-mini/.env）。

## 注意
- run intermediates（snapshot_raw / seed_plan / suggestion_plan）は追跡しない（.gitignore 対象）。証跡として残すのは approved_plan.json と *bundle*.yaml が基本。
- mode=pr では PR_BOT_TOKEN（Fine-grained PAT）を推奨。未設定だと required checks が PR で止まる場合がある。
