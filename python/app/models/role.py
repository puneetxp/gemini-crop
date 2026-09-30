from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from datetime import datetime as _datetime


class Role(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    name: str


class RoleInput(BaseModel):
    enable: int | None = None
    name: str | None = None
