from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class CropMilestone(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    stage: str
    expected_start_date: date
    expected_end_date: date
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: str | None = None
    progress_percentage: int | None = None
    recommendations: str | None = None
    notes: str | None = None
    alert_sent: bool | None = None
    crop_id: int


class CropMilestoneInput(BaseModel):
    enable: int | None = None
    stage: str | None = None
    expected_start_date: _date | None = None
    expected_end_date: _date | None = None
    actual_start_date: _date | None = None
    actual_end_date: _date | None = None
    status: str | None = None
    progress_percentage: int | None = None
    recommendations: str | None = None
    notes: str | None = None
    alert_sent: bool | None = None
    crop_id: int | None = None
