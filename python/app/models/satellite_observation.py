from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class SatelliteObservation(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    scene_id: str
    observed_on: date
    source: str
    ndvi: float | None = None
    ndmi: float | None = None
    ndre: float | None = None
    clear_pct: float | None = None
    pixels: int | None = None
    state: str | None = None
    district: str | None = None
    farm_id: int


class SatelliteObservationInput(BaseModel):
    enable: int | None = None
    scene_id: str | None = None
    observed_on: _date | None = None
    source: str | None = None
    ndvi: float | None = None
    ndmi: float | None = None
    ndre: float | None = None
    clear_pct: float | None = None
    pixels: int | None = None
    state: str | None = None
    district: str | None = None
    farm_id: int | None = None
