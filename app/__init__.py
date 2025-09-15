from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.routes_tasks import router as tasks_router

app = FastAPI()
app.include_router(tasks_router)

templates = Jinja2Templates(directory="app/ui/templates")


@app.get("/ui/task", response_class=HTMLResponse)
async def ui_task(req: Request):
    return templates.TemplateResponse("task_form.html", {"request": req})
