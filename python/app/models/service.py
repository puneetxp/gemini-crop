from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class Service(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    category: str
    name: str
    organisation: str | None = None
    description: str | None = None
    phone: str
    whatsapp: str | None = None
    email: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    address: str | None = None
    languages: str | None = None
    available_now: bool
    verified: bool
    is_active: bool
    added_by_user_id: int | None = None
    user_id: int | None = None


class ServiceInput(BaseModel):
    enable: int | None = None
    category: str | None = None
    name: str | None = None
    organisation: str | None = None
    description: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    address: str | None = None
    languages: str | None = None
    available_now: bool | None = None
    verified: bool | None = None
    is_active: bool | None = None
    added_by_user_id: int | None = None
    user_id: int | None = None
