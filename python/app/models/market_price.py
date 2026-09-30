from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class MarketPrice(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    item_type: str
    item_name: str
    variety: str | None = None
    price_per_unit: float
    quantity: float
    total_value: float
    quality_grade: str | None = None
    quality_premium_percent: float | None = None
    state: str
    district: str
    transaction_date: datetime
    season: str | None = None
    source: str
    listing_id: int | None = None
    booking_id: int | None = None
    transaction_id: int | None = None


class MarketPriceInput(BaseModel):
    enable: int | None = None
    item_type: str | None = None
    item_name: str | None = None
    variety: str | None = None
    price_per_unit: float | None = None
    quantity: float | None = None
    total_value: float | None = None
    quality_grade: str | None = None
    quality_premium_percent: float | None = None
    state: str | None = None
    district: str | None = None
    transaction_date: _datetime | None = None
    season: str | None = None
    source: str | None = None
    listing_id: int | None = None
    booking_id: int | None = None
    transaction_id: int | None = None
