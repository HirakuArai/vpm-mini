# Token Inventory (SSOT)
| Display Name | Type | Perms | Bound Repo(s) | Where used | Owner | Rotate | Notes |
|---|---|---|---|---|---|---|---|
| render-bot | classic | repo,workflow | * | GH_TOKEN (local/Codex), dispatch | Hiraku | 2026-01 | Primary execution token |
| fgpat_vpm-mini_ops-AWCP_20251009 | fine-grained | ActionsRW,ContentsRW,PRRW | HirakuArai/vpm-mini | GH_TOKEN_FG (Codex routine ops) | Hiraku | 2025-12 | Merge; 20251008 slated for revoke |
| claude_write_token | classic | repo | * | (deprecated) | Hiraku | revoke | Expiring; replace with render-bot |
| openai-bot-ci | (tbd) | (tbd) | (tbd) | (tbd) | (tbd) | (tbd) | Decide keep/revoke |
