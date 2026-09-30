from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from datetime import datetime as _datetime


class ActiveRole(BaseModel):
    id: int
    updated_at: datetime
    enable: int
    user_id: int
    role_id: int


class ActiveRoleInput(BaseModel):
    enable: int | None = None
    user_id: int | None = None
    role_id: int | None = None
