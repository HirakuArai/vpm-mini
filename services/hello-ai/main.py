from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "hello-ai from vpm-mini"}


@app.get("/healthz")
def healthz():
    return {"ok": True}
