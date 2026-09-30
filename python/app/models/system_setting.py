from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class SystemSetting(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    key: str
    value: str
    description: str | None = None


class SystemSettingInput(BaseModel):
    enable: int | None = None
    key: str | None = None
    value: str | None = None
    description: str | None = None
