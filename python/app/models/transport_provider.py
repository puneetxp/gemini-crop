from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class TransportProvider(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    company_name: str
    contact_person: str
    contact_phone: str
    contact_email: str | None = None
    service_areas: str
    vehicle_types: str
    livestock_specialization: str | None = None
    base_rate_per_km: float
    minimum_charge: float
    insurance_available: bool | None = None
    insurance_rate_percentage: float | None = None
    max_capacity_animals: int
    rating: float | None = None
    total_ratings: int | None = None
    completed_transports: int | None = None
    verified: bool | None = None
    verification_documents: str | None = None
    license_number: str | None = None
    status: str | None = None
    user_id: int


class TransportProviderInput(BaseModel):
    enable: int | None = None
    company_name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    service_areas: str | None = None
    vehicle_types: str | None = None
    livestock_specialization: str | None = None
    base_rate_per_km: float | None = None
    minimum_charge: float | None = None
    insurance_available: bool | None = None
    insurance_rate_percentage: float | None = None
    max_capacity_animals: int | None = None
    rating: float | None = None
    total_ratings: int | None = None
    completed_transports: int | None = None
    verified: bool | None = None
    verification_documents: str | None = None
    license_number: str | None = None
    status: str | None = None
    user_id: int | None = None
