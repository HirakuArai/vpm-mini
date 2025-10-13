# P2-3 Evidence: rougel-exporter KService
- READY: True
- URL: http://rougel-exporter.default.127.0.0.1.sslip.io
```

NAME                                                READY   STATUS    RESTARTS   AGE    IP            NODE                     NOMINATED NODE   READINESS GATES
rougel-exporter-00003-deployment-676fc8d966-gx8jr   2/2     Running   0          114s   10.244.0.59   vpm-mini-control-plane   <none>           <none>
```


## Re-published as multi-arch (amd64 present) @ 20251013_092931
- Image: ghcr.io/hirakuarai/rougel-exporter:latest
- READY: True
```
NAME                                                READY   STATUS             RESTARTS       AGE     IP            NODE                     NOMINATED NODE   READINESS GATES
rougel-exporter-00007-deployment-78d569cf77-52p52   0/2     CrashLoopBackOff   6 (4m5s ago)   10m     10.244.0.67   vpm-mini-control-plane   <none>           <none>
rougel-exporter-00008-deployment-78cf8cb55f-hqmdc   1/2     Terminating        0              5m51s   10.244.0.68   vpm-mini-control-plane   <none>           <none>
rougel-exporter-00009-deployment-664866c7d-5w56c    0/2     Completed          6 (3m3s ago)   5m51s   10.244.0.69   vpm-mini-control-plane   <none>           <none>
rougel-exporter-00010-deployment-6cf695d784-qmqnk   2/2     Running            0              112s    10.244.0.70   vpm-mini-control-plane   <none>           <none>
```
