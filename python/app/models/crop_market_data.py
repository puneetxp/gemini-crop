from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class CropMarketData(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_name: str
    state: str
    district: str | None = None
    price_per_kg: float
    date: date
    season: str
    yoy_growth: float | None = None
    demand_level: str | None = None


class CropMarketDataInput(BaseModel):
    enable: int | None = None
    crop_name: str | None = None
    state: str | None = None
    district: str | None = None
    price_per_kg: float | None = None
    date: _date | None = None
    season: str | None = None
    yoy_growth: float | None = None
    demand_level: str | None = None
