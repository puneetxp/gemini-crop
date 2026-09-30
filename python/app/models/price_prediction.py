from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class PricePrediction(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    item_type: str
    item_name: str
    variety: str | None = None
    state: str
    district: str | None = None
    prediction_date: datetime
    target_date: date
    predicted_price: float
    confidence_score: float
    price_range_min: float | None = None
    price_range_max: float | None = None
    trend: str | None = None
    demand_forecast: str | None = None
    supply_forecast: str | None = None
    season: str | None = None
    model_version: str | None = None
    factors: str | None = None


class PricePredictionInput(BaseModel):
    enable: int | None = None
    item_type: str | None = None
    item_name: str | None = None
    variety: str | None = None
    state: str | None = None
    district: str | None = None
    prediction_date: _datetime | None = None
    target_date: _date | None = None
    predicted_price: float | None = None
    confidence_score: float | None = None
    price_range_min: float | None = None
    price_range_max: float | None = None
    trend: str | None = None
    demand_forecast: str | None = None
    supply_forecast: str | None = None
    season: str | None = None
    model_version: str | None = None
    factors: str | None = None
