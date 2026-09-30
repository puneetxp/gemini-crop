from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class WeatherAlert(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    state: str
    district: str | None = None
    alert_type: str
    severity: str
    message: str
    recommendation: str | None = None
    valid_from: datetime
    valid_until: datetime
    is_active: bool | None = None
    farm_id: int | None = None


class WeatherAlertInput(BaseModel):
    enable: int | None = None
    state: str | None = None
    district: str | None = None
    alert_type: str | None = None
    severity: str | None = None
    message: str | None = None
    recommendation: str | None = None
    valid_from: _datetime | None = None
    valid_until: _datetime | None = None
    is_active: bool | None = None
    farm_id: int | None = None
