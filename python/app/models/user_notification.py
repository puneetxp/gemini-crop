from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from datetime import datetime as _datetime


class UserNotification(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    title: str
    message: str
    type: str
    link: str | None = None
    data: Dict[str, Any] | None = None
    is_read: bool
    read_at: datetime | None = None
    user_id: int


class UserNotificationInput(BaseModel):
    enable: int | None = None
    title: str | None = None
    message: str | None = None
    type: str | None = None
    link: str | None = None
    data: Dict[str, Any] | None = None
    is_read: bool | None = None
    read_at: _datetime | None = None
    user_id: int | None = None
