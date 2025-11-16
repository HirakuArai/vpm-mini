# metrics-echo READY Snapshot (P3-2 / Phase 3)

context_header: repo=vpm-mini / branch=main / phase=Phase 3 / track=P3-2 metrics-echo

本レポートは、Issue #774 (P3-2: metrics-echo minimal SLI /ask retry) に向けて、
metrics-echo KService の READY 状態を記録したスナップショットである。

## 1. Raw ksvc yaml

namespace: `default`

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"serving.knative.dev/v1","kind":"Service","metadata":{"annotations":{},"name":"metrics-echo","namespace":"default"},"spec":{"template":{"spec":{"containers":[{"env":[{"name":"TARGET","value":"vpm-mini"}],"image":"ghcr.io/hirakuarai/metrics-echo:dev"}]}}}}
    serving.knative.dev/creator: kubernetes-admin
    serving.knative.dev/lastModifier: kubernetes-admin
  creationTimestamp: "2025-11-10T01:53:41Z"
  generation: 1
  name: metrics-echo
  namespace: default
  resourceVersion: "58128"
  uid: 8b0d6dcc-f9b6-4bd7-8f1b-6f47f761fd3b
spec:
  template:
    metadata:
      creationTimestamp: null
    spec:
      containerConcurrency: 0
      containers:
      - env:
        - name: TARGET
          value: vpm-mini
        image: ghcr.io/hirakuarai/metrics-echo:dev
        name: user-container
        readinessProbe:
          successThreshold: 1
          tcpSocket:
            port: 0
        resources: {}
      enableServiceLinks: false
      timeoutSeconds: 300
  traffic:
  - latestRevision: true
    percent: 100
status:
  address:
    url: http://metrics-echo.default.svc.cluster.local
  conditions:
  - lastTransitionTime: "2025-11-10T01:54:13Z"
    status: "True"
    type: ConfigurationsReady
  - lastTransitionTime: "2025-11-10T01:54:18Z"
    status: "True"
    type: Ready
  - lastTransitionTime: "2025-11-10T01:54:18Z"
    status: "True"
    type: RoutesReady
  latestCreatedRevisionName: metrics-echo-00001
  latestReadyRevisionName: metrics-echo-00001
  observedGeneration: 1
  traffic:
  - latestRevision: true
    percent: 100
    revisionName: metrics-echo-00001
  url: http://metrics-echo.default.127.0.0.1.nip.io
```

## 2. 備考

- 本レポートは Issue #774 の「READY 側 Evidence」の第一ステップとして作成。
- 成功率（SLI）や /ask 実行は別の PR / レポートで扱う予定。
