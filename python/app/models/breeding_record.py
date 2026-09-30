from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class BreedingRecord(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    breeding_type: str
    breeding_date: date
    mate_breed: str | None = None
    expected_delivery_date: date | None = None
    actual_delivery_date: date | None = None
    pregnancy_status: str
    number_of_offspring: int | None = None
    breeding_cost: float | None = None
    veterinarian_name: str | None = None
    notes: str | None = None
    livestock_id: int
    farmer_id: int
    mate_id: int | None = None


class BreedingRecordInput(BaseModel):
    enable: int | None = None
    breeding_type: str | None = None
    breeding_date: _date | None = None
    mate_breed: str | None = None
    expected_delivery_date: _date | None = None
    actual_delivery_date: _date | None = None
    pregnancy_status: str | None = None
    number_of_offspring: int | None = None
    breeding_cost: float | None = None
    veterinarian_name: str | None = None
    notes: str | None = None
    livestock_id: int | None = None
    farmer_id: int | None = None
    mate_id: int | None = None
