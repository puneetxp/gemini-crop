from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class MspRate(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_name: str
    year: int
    season: str
    msp_per_quintal: float
    msp_per_kg: float | None = None
    increase_over_previous: float | None = None
    cost_of_production: float | None = None
    return_over_cost_percent: float | None = None
    source: str | None = None


class MspRateInput(BaseModel):
    enable: int | None = None
    crop_name: str | None = None
    year: int | None = None
    season: str | None = None
    msp_per_quintal: float | None = None
    msp_per_kg: float | None = None
    increase_over_previous: float | None = None
    cost_of_production: float | None = None
    return_over_cost_percent: float | None = None
    source: str | None = None
