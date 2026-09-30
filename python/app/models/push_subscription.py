from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class PushSubscription(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    user_id: int
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None


class PushSubscriptionInput(BaseModel):
    enable: int | None = None
    user_id: int | None = None
    endpoint: str | None = None
    p256dh: str | None = None
    auth: str | None = None
    user_agent: str | None = None
