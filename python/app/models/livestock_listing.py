from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class LivestockListing(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    title: str
    description: str | None = None
    species: str
    breed: str
    age_years: int | None = None
    age_months: int | None = None
    gender: str
    quantity: int
    purpose: str
    price: float
    price_negotiable: bool | None = None
    weight_kg: float | None = None
    health_status: str | None = None
    vaccination_status: str | None = None
    last_vaccination_date: date | None = None
    milk_production_liters: float | None = None
    breeding_certified: bool | None = None
    breeding_certification_number: str | None = None
    genetic_lineage: str | None = None
    photos: str | None = None
    videos: str | None = None
    location_state: str
    location_district: str
    location_village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pincode: str | None = None
    address_line: str | None = None
    farmer_contact_phone: str | None = None
    farmer_contact_email: str | None = None
    status: str | None = None
    views_count: int | None = None
    interest_count: int | None = None
    inquiry_count: int | None = None
    featured: bool | None = None
    featured_until: datetime | None = None
    livestock_id: int
    farmer_id: int


class LivestockListingInput(BaseModel):
    enable: int | None = None
    title: str | None = None
    description: str | None = None
    species: str | None = None
    breed: str | None = None
    age_years: int | None = None
    age_months: int | None = None
    gender: str | None = None
    quantity: int | None = None
    purpose: str | None = None
    price: float | None = None
    price_negotiable: bool | None = None
    weight_kg: float | None = None
    health_status: str | None = None
    vaccination_status: str | None = None
    last_vaccination_date: _date | None = None
    milk_production_liters: float | None = None
    breeding_certified: bool | None = None
    breeding_certification_number: str | None = None
    genetic_lineage: str | None = None
    photos: str | None = None
    videos: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    location_village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pincode: str | None = None
    address_line: str | None = None
    farmer_contact_phone: str | None = None
    farmer_contact_email: str | None = None
    status: str | None = None
    views_count: int | None = None
    interest_count: int | None = None
    inquiry_count: int | None = None
    featured: bool | None = None
    featured_until: _datetime | None = None
    livestock_id: int | None = None
    farmer_id: int | None = None
