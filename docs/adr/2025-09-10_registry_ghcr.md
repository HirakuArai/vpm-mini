# ADR: Use GitHub Container Registry (GHCR) as canonical image registry
- Date: 2025-09-10
- Decision: ghcr.io/HirakuArai/<service>
- Scope: hello-ai (and subsequent services) under vpm-mini
- Rationale: GitHub との権限一体化、CI/CD 連携、Image Updater 自動追従の最小コスト化
- Consequences:
  - Argo CD Image Updater は ghcr.io/HirakuArai/hello-ai を追跡
  - ko.local は overlay/local 限定。overlay/dev/prod では禁止
- Status: Accepted