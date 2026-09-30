from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class Livestock(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    species: str
    breed: str
    name: str | None = None
    quantity: int
    purchase_price: float
    purchase_date: date
    purpose: str
    expected_roi: float | None = None
    break_even_date: date | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pincode: str | None = None
    state: str | None = None
    district: str | None = None
    village: str | None = None
    address_line: str | None = None
    farm_id: int
    farmer_id: int


class LivestockInput(BaseModel):
    enable: int | None = None
    species: str | None = None
    breed: str | None = None
    name: str | None = None
    quantity: int | None = None
    purchase_price: float | None = None
    purchase_date: _date | None = None
    purpose: str | None = None
    expected_roi: float | None = None
    break_even_date: _date | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pincode: str | None = None
    state: str | None = None
    district: str | None = None
    village: str | None = None
    address_line: str | None = None
    farm_id: int | None = None
    farmer_id: int | None = None
