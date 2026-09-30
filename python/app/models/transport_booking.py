from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class TransportBooking(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    pickup_address: str
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    delivery_address: str
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    distance_km: float
    livestock_type: str
    livestock_count: int
    animal_value: float
    transport_cost: float
    insurance_opted: bool | None = None
    insurance_cost: float | None = None
    total_cost: float
    scheduled_pickup_date: datetime
    estimated_delivery_date: datetime
    actual_pickup_date: datetime | None = None
    actual_delivery_date: datetime | None = None
    status: str | None = None
    tracking_updates: str | None = None
    special_instructions: str | None = None
    rating: int | None = None
    review: str | None = None
    reviewed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    transaction_id: int
    provider_id: int
    requester_id: int


class TransportBookingInput(BaseModel):
    enable: int | None = None
    pickup_address: str | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    distance_km: float | None = None
    livestock_type: str | None = None
    livestock_count: int | None = None
    animal_value: float | None = None
    transport_cost: float | None = None
    insurance_opted: bool | None = None
    insurance_cost: float | None = None
    total_cost: float | None = None
    scheduled_pickup_date: _datetime | None = None
    estimated_delivery_date: _datetime | None = None
    actual_pickup_date: _datetime | None = None
    actual_delivery_date: _datetime | None = None
    status: str | None = None
    tracking_updates: str | None = None
    special_instructions: str | None = None
    rating: int | None = None
    review: str | None = None
    reviewed_at: _datetime | None = None
    cancelled_at: _datetime | None = None
    cancellation_reason: str | None = None
    transaction_id: int | None = None
    provider_id: int | None = None
    requester_id: int | None = None
