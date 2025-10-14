# P2-3 metrics-echo Evidence @ 20251014_060618

## ksvc (READY=True)
NAME           URL                                              LATESTCREATED        LATESTREADY          READY   REASON
metrics-echo   http://metrics-echo.default.127.0.0.1.sslip.io   metrics-echo-00007   metrics-echo-00007   True    

## kservice yaml head
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"serving.knative.dev/v1","kind":"Service","metadata":{"annotations":{},"name":"metrics-echo","namespace":"default"},"spec":{"template":{"metadata":{"annotations":{"autoscaling.knative.dev/maxScale":"10","autoscaling.knative.dev/minScale":"0"}},"spec":{"containers":[{"env":[{"name":"APP_NAME","value":"metrics-echo"}],"image":"ghcr.io/hirakuarai/metrics-echo:latest","imagePullPolicy":"IfNotPresent","name":"app","ports":[{"containerPort":8080,"protocol":"TCP"}],"readinessProbe":{"httpGet":{"path":"/healthz","port":8080},"initialDelaySeconds":2,"periodSeconds":5},"resources":{"limits":{"cpu":"200m","memory":"256Mi"},"requests":{"cpu":"50m","memory":"64Mi"}}}],"enableServiceLinks":false,"timeoutSeconds":300}}}}
    serving.knative.dev/creator: kubernetes-admin
    serving.knative.dev/lastModifier: kubernetes-admin
  creationTimestamp: "2025-10-13T19:03:07Z"
  generation: 7
  name: metrics-echo
  namespace: default
  resourceVersion: "167432"
  uid: 42027a05-1bf7-4257-b6ac-df98379242ab
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/minScale: "0"
        rollout-ts: "1760389306"
      creationTimestamp: null
    spec:
      containerConcurrency: 0
      containers:
      - env:
        - name: APP_NAME
          value: metrics-echo
        image: ghcr.io/hirakuarai/metrics-echo:latest
        imagePullPolicy: IfNotPresent
        name: app
        ports:
        - containerPort: 8080
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 2
          periodSeconds: 5
          successThreshold: 1
          timeoutSeconds: 1
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 50m
            memory: 64Mi
      enableServiceLinks: false
      timeoutSeconds: 300
  traffic:
  - latestRevision: true
    percent: 100
status:
  address:
    url: http://metrics-echo.default.svc.cluster.local
  conditions:
  - lastTransitionTime: "2025-10-13T21:01:56Z"
    status: "True"
    type: ConfigurationsReady
  - lastTransitionTime: "2025-10-13T21:01:57Z"
    status: "True"
    type: Ready
  - lastTransitionTime: "2025-10-13T21:01:57Z"
    status: "True"
    type: RoutesReady
  latestCreatedRevisionName: metrics-echo-00007
  latestReadyRevisionName: metrics-echo-00007
  observedGeneration: 7
  traffic:
  - latestRevision: true
    percent: 100
    revisionName: metrics-echo-00007
  url: http://metrics-echo.default.127.0.0.1.sslip.io

## GHCR tags (head)
{"message":"Resource not accessible by personal access token","documentation_url":"https://docs.github.com/rest/packages/packages#list-package-versions-for-a-package-owned-by-a-user","status":"403"}<requires read:packages>

## In-cluster curl
\`curl -sS http://metrics-echo.default.svc.cluster.local/healthz\` -> {"status":"ok"}
