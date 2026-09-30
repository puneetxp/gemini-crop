from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class QualityVerification(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    verification_date: datetime
    verifier_type: str
    quality_grade: str
    quality_metrics: str | None = None
    photos: str | None = None
    passed: bool
    notes: str | None = None
    booking_id: int


class QualityVerificationInput(BaseModel):
    enable: int | None = None
    verification_date: _datetime | None = None
    verifier_type: str | None = None
    quality_grade: str | None = None
    quality_metrics: str | None = None
    photos: str | None = None
    passed: bool | None = None
    notes: str | None = None
    booking_id: int | None = None
