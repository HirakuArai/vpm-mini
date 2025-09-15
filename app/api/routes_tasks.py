from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime

from app.core.models import TaskIn, TaskOut
from app.core.tracing import gen_trace_id
from app.core.evidence import write_evidence

router = APIRouter()


@router.post("/api/v1/tasks", response_model=TaskOut, status_code=201)
async def create_task(req: Request, data: TaskIn):
    trace_id = gen_trace_id()
    meta = {
        "remote_addr": req.client.host if req.client else None,
        "user_agent": req.headers.get("user-agent"),
    }
    write_evidence(trace_id, {"input": data.model_dump(), "meta": meta})
    out = TaskOut(
        trace_id=trace_id, created_at=datetime.datetime.utcnow().isoformat() + "Z"
    )
    return JSONResponse(out.model_dump())
