from pydantic import BaseModel, Field
from typing import Literal, List


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Literal["low", "mid", "high"] = "mid"
    tags: List[str] = []


class TaskOut(BaseModel):
    trace_id: str
    created_at: str
