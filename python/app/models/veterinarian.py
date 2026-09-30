from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class Veterinarian(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    added_by_user_id: int | None = None
    name: str
    clinic_name: str | None = None
    specialization: str | None = None
    species_supported: str | None = None
    phone: str
    whatsapp: str | None = None
    email: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    address: str | None = None
    available_now: bool
    verified: bool
    rating: float | None = None
    total_ratings: int | None = None
    notes: str | None = None


class VeterinarianInput(BaseModel):
    enable: int | None = None
    added_by_user_id: int | None = None
    name: str | None = None
    clinic_name: str | None = None
    specialization: str | None = None
    species_supported: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    address: str | None = None
    available_now: bool | None = None
    verified: bool | None = None
    rating: float | None = None
    total_ratings: int | None = None
    notes: str | None = None
