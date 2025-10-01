# Evidence: P2-3 dev monitoring monitoring-dev namespace

- Purpose: Add a minimal dev monitoring namespace via kustomize overlay so `k8s-validate` can lint the manifests.
- Files:
  - infra/k8s/overlays/dev/monitoring/kustomization.yaml
  - infra/k8s/overlays/dev/monitoring/namespace.yaml
- CI Run: Run: https://github.com/HirakuArai/vpm-mini/actions/runs/18170877978 (update with `k8s-validate` success URL once available)

## Notes
- Namespace only; no service deployments included at this stage.
- Ensure the follow-up CI run completes successfully before merging.
