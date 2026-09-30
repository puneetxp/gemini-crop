from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class AdvanceBooking(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    quantity_booked: float
    price_per_unit: float
    total_amount: float
    advance_payment_percent: int
    advance_payment_amount: float
    booking_date: datetime
    expected_delivery_date: datetime
    status: str
    quality_standards: str | None = None
    contract_terms: str | None = None
    listing_id: int
    buyer_id: int
    farmer_id: int


class AdvanceBookingInput(BaseModel):
    enable: int | None = None
    quantity_booked: float | None = None
    price_per_unit: float | None = None
    total_amount: float | None = None
    advance_payment_percent: int | None = None
    advance_payment_amount: float | None = None
    booking_date: _datetime | None = None
    expected_delivery_date: _datetime | None = None
    status: str | None = None
    quality_standards: str | None = None
    contract_terms: str | None = None
    listing_id: int | None = None
    buyer_id: int | None = None
    farmer_id: int | None = None
