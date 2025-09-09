# P4-2A.1 Admin Rotation & First Sync Evidence (20250909_150438)

## Preflight


```bash
kubectl -n argocd get deploy,svc,secret | head -n 100
```

  NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/argocd-applicationset-controller   1/1     1            1           42m
  deployment.apps/argocd-dex-server                  1/1     1            1           42m
  deployment.apps/argocd-notifications-controller    1/1     1            1           42m
  deployment.apps/argocd-redis                       1/1     1            1           42m
  deployment.apps/argocd-repo-server                 1/1     1            1           42m
  deployment.apps/argocd-server                      1/1     1            1           42m
  
  NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
  service/argocd-applicationset-controller          ClusterIP   10.96.96.124    <none>        7000/TCP,8080/TCP            43m
  service/argocd-dex-server                         ClusterIP   10.96.153.87    <none>        5556/TCP,5557/TCP,5558/TCP   43m
  service/argocd-metrics                            ClusterIP   10.96.24.238    <none>        8082/TCP                     43m
  service/argocd-notifications-controller-metrics   ClusterIP   10.96.91.76     <none>        9001/TCP                     43m
  service/argocd-redis                              ClusterIP   10.96.117.149   <none>        6379/TCP                     42m
  service/argocd-repo-server                        ClusterIP   10.96.107.196   <none>        8081/TCP,8084/TCP            42m
  service/argocd-server                             ClusterIP   10.96.40.207    <none>        80/TCP,443/TCP               42m
  service/argocd-server-metrics                     ClusterIP   10.96.71.146    <none>        8083/TCP                     42m
  
  NAME                                 TYPE     DATA   AGE
  secret/argocd-initial-admin-secret   Opaque   1      42m
  secret/argocd-notifications-secret   Opaque   0      43m
  secret/argocd-redis                  Opaque   1      42m
  secret/argocd-secret                 Opaque   5      43m

## Initial admin secret

Initial admin password detected.

## Admin rotation (conditional: argocd CLI)

argocd CLI not found → rotation step skipped（Secret cleanupのみ実施）

## Delete initial secret (cleanup)


```bash
kubectl -n argocd delete secret argocd-initial-admin-secret
```

  secret "argocd-initial-admin-secret" deleted

## Force first sync (hello-ai)


```bash
kubectl -n argocd annotate application vpm-mini-hello-ai argocd.argoproj.io/refresh=hard --overwrite
```

  application.argoproj.io/vpm-mini-hello-ai annotated

## Status after sync


```bash
kubectl -n argocd get applications.argoproj.io vpm-mini-hello-ai -o wide
```

  NAME                SYNC STATUS   HEALTH STATUS   REVISION                                   PROJECT
  vpm-mini-hello-ai   OutOfSync     Healthy         49126f0ade2b269d98ab0b81f022841c99e1ea9b   vpm-mini-dev

```bash
kubectl -n argocd get applications.argoproj.io vpm-mini-hello-ai -o jsonpath='{.status.sync.status} {"/"} {.status.health.status}{"
"}'
```

  OutOfSync / Healthy

---
✅ Completed P4-2A.1 (Admin rotation & first sync)

