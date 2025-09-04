# P3-1 Guardrails (AllowedRepos) Evidence - 20250905_041616

## Attempt: patch hello-ai to docker.io/kennethreitz/httpbin:latest (expect DENY)

RC=1 (0=allowed / non-zero=denied)



RC=Error from server (InternalError): Internal error occurred: failed calling webhook "webhook.serving.knative.dev": failed to call webhook: Post "https://webhook.knative-serving.svc:443/defaulting?timeout=10s": context deadline exceeded (0=allowed / non-zero=denied)


