from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class BuyerInterest(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    buyer_name: str
    buyer_phone: str
    buyer_email: str | None = None
    buyer_type: str
    interested_quantity: int
    message: str | None = None
    status: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_state: str | None = None
    delivery_district: str | None = None
    delivery_village: str | None = None
    delivery_address_line: str | None = None
    listing_id: int


class BuyerInterestInput(BaseModel):
    enable: int | None = None
    buyer_name: str | None = None
    buyer_phone: str | None = None
    buyer_email: str | None = None
    buyer_type: str | None = None
    interested_quantity: int | None = None
    message: str | None = None
    status: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_state: str | None = None
    delivery_district: str | None = None
    delivery_village: str | None = None
    delivery_address_line: str | None = None
    listing_id: int | None = None
