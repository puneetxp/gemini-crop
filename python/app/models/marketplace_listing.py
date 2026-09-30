from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class MarketplaceListing(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_type: str
    crop_variety: str | None = None
    expected_harvest_date: date
    estimated_quantity: int
    available_quantity: int | None = None
    quality_grade: str | None = None
    location_state: str
    location_district: str
    farmer_contact_phone: str | None = None
    farmer_contact_email: str | None = None
    status: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_village: str | None = None
    delivery_address_line: str | None = None
    embedding: str | None = None
    embedding_cache_key: str | None = None
    price_per_unit: float | None = None
    farm_id: int
    farmer_id: int


class MarketplaceListingInput(BaseModel):
    enable: int | None = None
    crop_type: str | None = None
    crop_variety: str | None = None
    expected_harvest_date: _date | None = None
    estimated_quantity: int | None = None
    available_quantity: int | None = None
    quality_grade: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    farmer_contact_phone: str | None = None
    farmer_contact_email: str | None = None
    status: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    delivery_pincode: str | None = None
    delivery_village: str | None = None
    delivery_address_line: str | None = None
    embedding: str | None = None
    embedding_cache_key: str | None = None
    price_per_unit: float | None = None
    farm_id: int | None = None
    farmer_id: int | None = None
