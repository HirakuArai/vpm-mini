# P5-4 Vault(K8sAuth) verification (dev)
- datetime(UTC): 2025-09-16T17:19:16Z
- context: kind-kind

## Vault Installation
- Namespace: vault
- Version: HashiCorp Vault v1.20.1
- Status: Running and unsealed
- Authentication: Kubernetes auth enabled with role `eso-demo`

## ExternalSecret (secrets-system/demo-api-key)
```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: demo-api-key
  namespace: secrets-system
spec:
  data:
  - remoteRef:
      conversionStrategy: Default
      decodingStrategy: None
      key: demo
      metadataPolicy: None
      property: api-key
    secretKey: api-key  # pragma: allowlist secret
  refreshInterval: 1m
  secretStoreRef:
    kind: SecretStore
    name: vault-store
  target:
    creationPolicy: Owner
    deletionPolicy: Retain
    name: demo-synced
status:
  binding:
    name: demo-synced
  conditions:
  - lastTransitionTime: "2025-09-16T17:16:55Z"
    message: Secret was synced
    reason: SecretSynced
    status: "True"
    type: Ready
  refreshTime: "2025-09-16T17:16:55Z"
  syncedResourceVersion: "1-b98a479e91f2eb88c659bf5e2a638b63cd3a37e3ca93419701c3c582"
```

## Synced Secret
- name: secrets-system/demo-synced  # pragma: allowlist secret
- api-key (decoded): trial-1758042784

## End-to-End Verification
- ✅ Vault installed and running
- ✅ Vault initialized and unsealed
- ✅ kv-v2 secrets engine enabled at path `secret/`
- ✅ Policy `eso-demo` created with read access
- ✅ Kubernetes auth configured with role `eso-demo`
- ✅ SecretStore `vault-store` connected to Vault successfully
- ✅ ExternalSecret syncing from Vault path `secret/data/demo`
- ✅ K8s Secret `demo-synced` created with correct value from Vault

## DoD
- [x] ExternalSecret Ready=True
- [x] demo-synced value present (non-empty)
- [x] End-to-end Vault integration verified