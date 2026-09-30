from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class SupplyMatch(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    matched_quantity: float
    match_score: float | None = None
    price_offered: float | None = None
    status: str
    match_explanation: str | None = None
    is_aggregated: bool
    aggregation_group_id: str | None = None
    farmer_confirmation_status: str
    farmer_confirmed_at: datetime | None = None
    buyer_accepted_at: datetime | None = None
    delivery_status: str
    delivery_notes: str | None = None
    request_id: int
    listing_id: int | None = None
    farmer_id: int


class SupplyMatchInput(BaseModel):
    enable: int | None = None
    matched_quantity: float | None = None
    match_score: float | None = None
    price_offered: float | None = None
    status: str | None = None
    match_explanation: str | None = None
    is_aggregated: bool | None = None
    aggregation_group_id: str | None = None
    farmer_confirmation_status: str | None = None
    farmer_confirmed_at: _datetime | None = None
    buyer_accepted_at: _datetime | None = None
    delivery_status: str | None = None
    delivery_notes: str | None = None
    request_id: int | None = None
    listing_id: int | None = None
    farmer_id: int | None = None
