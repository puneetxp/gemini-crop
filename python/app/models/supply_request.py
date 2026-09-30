from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class SupplyRequest(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_type: str
    quantity_needed: float
    quality_requirements: str | None = None
    delivery_date_start: datetime
    delivery_date_end: datetime
    max_price_per_unit: float | None = None
    recurring: bool
    recurrence_pattern: str | None = None
    is_emergency: bool
    status: str
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_state: str | None = None
    delivery_district: str | None = None
    notes: str | None = None
    embedding: str | None = None
    embedding_cache_key: str | None = None
    buyer_id: int


class SupplyRequestInput(BaseModel):
    enable: int | None = None
    crop_type: str | None = None
    quantity_needed: float | None = None
    quality_requirements: str | None = None
    delivery_date_start: _datetime | None = None
    delivery_date_end: _datetime | None = None
    max_price_per_unit: float | None = None
    recurring: bool | None = None
    recurrence_pattern: str | None = None
    is_emergency: bool | None = None
    status: str | None = None
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_state: str | None = None
    delivery_district: str | None = None
    notes: str | None = None
    embedding: str | None = None
    embedding_cache_key: str | None = None
    buyer_id: int | None = None
