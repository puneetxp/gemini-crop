from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class LivestockHealthRecord(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    record_type: str
    record_date: date
    description: str
    veterinarian_name: str | None = None
    cost: float | None = None
    next_due_date: date | None = None
    notes: str | None = None
    livestock_id: int


class LivestockHealthRecordInput(BaseModel):
    enable: int | None = None
    record_type: str | None = None
    record_date: _date | None = None
    description: str | None = None
    veterinarian_name: str | None = None
    cost: float | None = None
    next_due_date: _date | None = None
    notes: str | None = None
    livestock_id: int | None = None
