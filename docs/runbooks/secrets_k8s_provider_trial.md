# Secrets Trial: Kubernetes provider via External Secrets

- **Goal**: SecretStore (provider=kubernetes) → ExternalSecret → K8s Secret
- **Why**: No static creds; easy swap to Vault by replacing only SecretStore.

## Apply

```bash
kubectl apply -f infra/external-secrets/kubernetes/secretstore.yaml
```

## Prepare source secret once:

```bash
kubectl -n secrets-system create secret generic demo-source --from-literal=api-key=trial-$(date +%s) --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f infra/external-secrets/kubernetes/externalsecret_demo.yaml
```

## Verify

```bash
kubectl get externalsecret -A
kubectl -n default get secret demo-synced -o jsonpath='{.data.api-key}' | base64 -D
```