# Knative Webhook Triage @ 20250827-052951

## Cluster / Versions
error: unknown flag: --short
See 'kubectl version --help' for usage.
NAME                 STATUS   AGE
default              Active   44d
hyper-swarm          Active   44d
istio-system         Active   44d
knative-serving      Active   44d
kube-node-lease      Active   44d
kube-public          Active   44d
kube-system          Active   44d
local-path-storage   Active   44d

## knative-serving: deployments / pods
NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                                                                                                 SELECTOR
deployment.apps/activator              0/1     1            0           44d   activator    gcr.io/knative-releases/knative.dev/serving/cmd/activator@sha256:80b2e4bf6df496c692f8e148b3a72afcb88165cb7428e52b788fa53075989655      app=activator,role=activator
deployment.apps/autoscaler             0/1     1            0           44d   autoscaler   gcr.io/knative-releases/knative.dev/serving/cmd/autoscaler@sha256:6ff1f7816c67954f4533edd7a7e35882e2d52613cc3343594ff3eddfd0c1fca2     app=autoscaler
deployment.apps/controller             0/1     1            0           44d   controller   gcr.io/knative-releases/knative.dev/serving/cmd/controller@sha256:d4c6a0f926509e8d34795003635fdb8625dd3d4648ec55fe2ce781e0b8750e04     app=controller
deployment.apps/net-istio-controller   0/1     1            0           44d   controller   gcr.io/knative-releases/knative.dev/net-istio/cmd/controller@sha256:18376be76f77cd195e2bb4993eebf86c6b8c34222247f2f8e4a265c5c4e9b9a8   app=net-istio-controller
deployment.apps/net-istio-webhook      0/1     1            0           44d   webhook      gcr.io/knative-releases/knative.dev/net-istio/cmd/webhook@sha256:dcc32d23e1565c26620c3735c28ea294215e8b01dd9a30b58e19152879b89422      app=net-istio-webhook,role=net-istio-webhook
deployment.apps/webhook                0/1     1            0           44d   webhook      gcr.io/knative-releases/knative.dev/serving/cmd/webhook@sha256:6fb473eb7641c3f7174ed4064e6c3f5eeeb05e1420f5af425bbec33af53f4f92        app=webhook,role=webhook

NAME                                        READY   STATUS    RESTARTS      AGE   IP            NODE                  NOMINATED NODE   READINESS GATES
pod/activator-cbf5b6b55-cfd9t               1/1     Running   0             43d   10.244.0.5    swarm-control-plane   <none>           <none>
pod/autoscaler-c5d454c88-cvfwx              1/1     Running   0             43d   10.244.0.6    swarm-control-plane   <none>           <none>
pod/controller-76b7b86554-ng2mq             1/1     Running   2 (41d ago)   43d   10.244.0.8    swarm-control-plane   <none>           <none>
pod/net-istio-controller-574679cd5f-ztgqq   1/1     Running   0             43d   10.244.0.11   swarm-control-plane   <none>           <none>
pod/net-istio-webhook-85c99487db-q44kk      1/1     Running   0             43d   10.244.0.9    swarm-control-plane   <none>           <none>
pod/webhook-75d4fb6db5-httj4                1/1     Running   0             43d   10.244.0.7    swarm-control-plane   <none>           <none>

## kourier-system: deployments / pods (if any)

## CRDs (knative.dev)
12
certificates.networking.internal.knative.dev          2025-07-13T17:57:01Z
clusterdomainclaims.networking.internal.knative.dev   2025-07-13T17:57:01Z
configurations.serving.knative.dev                    2025-07-13T17:57:01Z
domainmappings.serving.knative.dev                    2025-07-13T17:57:01Z
images.caching.internal.knative.dev                   2025-07-13T17:57:01Z
ingresses.networking.internal.knative.dev             2025-07-13T17:57:01Z
metrics.autoscaling.internal.knative.dev              2025-07-13T17:57:01Z
podautoscalers.autoscaling.internal.knative.dev       2025-07-13T17:57:01Z
revisions.serving.knative.dev                         2025-07-13T17:57:01Z
routes.serving.knative.dev                            2025-07-13T17:57:01Z
serverlessservices.networking.internal.knative.dev    2025-07-13T17:57:01Z
services.serving.knative.dev                          2025-07-13T17:57:01Z

## Webhook configurations
validatingwebhookconfiguration.admissionregistration.k8s.io/config.webhook.istio.networking.internal.knative.dev   1          44d
validatingwebhookconfiguration.admissionregistration.k8s.io/config.webhook.serving.knative.dev                     1          44d
validatingwebhookconfiguration.admissionregistration.k8s.io/validation.webhook.serving.knative.dev                 1          44d
mutatingwebhookconfiguration.admissionregistration.k8s.io/webhook.istio.networking.internal.knative.dev   1          44d
mutatingwebhookconfiguration.admissionregistration.k8s.io/webhook.serving.knative.dev                     1          44d
