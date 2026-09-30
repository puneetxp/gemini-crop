from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class Offspring(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    birth_date: date
    gender: str | None = None
    birth_weight: float | None = None
    health_status: str
    current_weight: float | None = None
    growth_rate: float | None = None
    weaning_date: date | None = None
    sale_date: date | None = None
    sale_price: float | None = None
    notes: str | None = None
    breeding_record_id: int
    livestock_id: int | None = None
    farmer_id: int


class OffspringInput(BaseModel):
    enable: int | None = None
    birth_date: _date | None = None
    gender: str | None = None
    birth_weight: float | None = None
    health_status: str | None = None
    current_weight: float | None = None
    growth_rate: float | None = None
    weaning_date: _date | None = None
    sale_date: _date | None = None
    sale_price: float | None = None
    notes: str | None = None
    breeding_record_id: int | None = None
    livestock_id: int | None = None
    farmer_id: int | None = None
