from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class Crop(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_name: str
    crop_variety: str | None = None
    season: str
    planting_date: date
    expected_harvest_date: date
    area: float
    expected_yield: float | None = None
    expected_profit: float | None = None
    actual_yield: float | None = None
    actual_profit: float | None = None
    status: str | None = None
    parent_crop_id: int | None = None
    crop_role: str | None = None
    farm_plot_id: int
    strategy_id: int | None = None


class CropInput(BaseModel):
    enable: int | None = None
    crop_name: str | None = None
    crop_variety: str | None = None
    season: str | None = None
    planting_date: _date | None = None
    expected_harvest_date: _date | None = None
    area: float | None = None
    expected_yield: float | None = None
    expected_profit: float | None = None
    actual_yield: float | None = None
    actual_profit: float | None = None
    status: str | None = None
    parent_crop_id: int | None = None
    crop_role: str | None = None
    farm_plot_id: int | None = None
    strategy_id: int | None = None
