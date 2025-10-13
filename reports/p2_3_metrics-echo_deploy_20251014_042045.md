# P2-3 Evidence: metrics-echo KService
- READY: False (image pull pending)
- URL: http://metrics-echo.default.127.0.0.1.sslip.io

```
$(kubectl get ksvc metrics-echo -o wide)
```

## Notes
- Local image built and loaded: ghcr.io/hirakuarai/metrics-echo:latest
- Push to GHCR (multi-arch) still pending; run workflow or docker buildx to publish before final verification.
