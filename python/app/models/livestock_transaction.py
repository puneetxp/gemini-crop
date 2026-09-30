from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class LivestockTransaction(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    transaction_type: str
    quantity: int
    agreed_price: float
    status: str | None = None
    buyer_message: str | None = None
    seller_response: str | None = None
    buyer_contact_phone: str | None = None
    buyer_contact_email: str | None = None
    delivery_required: bool | None = None
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    health_guarantee_days: int | None = None
    health_guarantee_expires: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    notes: str | None = None
    listing_id: int
    seller_id: int
    buyer_id: int


class LivestockTransactionInput(BaseModel):
    enable: int | None = None
    transaction_type: str | None = None
    quantity: int | None = None
    agreed_price: float | None = None
    status: str | None = None
    buyer_message: str | None = None
    seller_response: str | None = None
    buyer_contact_phone: str | None = None
    buyer_contact_email: str | None = None
    delivery_required: bool | None = None
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    health_guarantee_days: int | None = None
    health_guarantee_expires: _datetime | None = None
    completed_at: _datetime | None = None
    cancelled_at: _datetime | None = None
    cancellation_reason: str | None = None
    notes: str | None = None
    listing_id: int | None = None
    seller_id: int | None = None
    buyer_id: int | None = None
