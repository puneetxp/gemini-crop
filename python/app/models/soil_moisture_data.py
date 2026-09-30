from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class SoilMoistureData(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    state: str
    district: str
    date: date
    year: int
    month: str
    moisture_level: float
    agency_name: str | None = None


class SoilMoistureDataInput(BaseModel):
    enable: int | None = None
    state: str | None = None
    district: str | None = None
    date: _date | None = None
    year: int | None = None
    month: str | None = None
    moisture_level: float | None = None
    agency_name: str | None = None
