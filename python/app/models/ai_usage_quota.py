from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class AiUsageQuota(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    date: date
    gps_enhanced_requests: int
    pincode_requests: int
    last_reset: datetime
    quota_limit: int
    user_id: int


class AiUsageQuotaInput(BaseModel):
    enable: int | None = None
    date: _date | None = None
    gps_enhanced_requests: int | None = None
    pincode_requests: int | None = None
    last_reset: _datetime | None = None
    quota_limit: int | None = None
    user_id: int | None = None
