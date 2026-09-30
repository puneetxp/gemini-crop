from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from datetime import datetime as _datetime


class CropDiagnosis(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_id: int | None = None
    farm_id: int | None = None
    crop_name: str | None = None
    state: str | None = None
    district: str | None = None
    disease_name: str | None = None
    scientific_name: str | None = None
    category: str | None = None
    severity: str | None = None
    urgency: str | None = None
    confidence: float | None = None
    language: str | None = None
    model_used: str | None = None
    safety_flags: int
    result: Dict[str, Any] | None = None
    user_id: int


class CropDiagnosisInput(BaseModel):
    enable: int | None = None
    crop_id: int | None = None
    farm_id: int | None = None
    crop_name: str | None = None
    state: str | None = None
    district: str | None = None
    disease_name: str | None = None
    scientific_name: str | None = None
    category: str | None = None
    severity: str | None = None
    urgency: str | None = None
    confidence: float | None = None
    language: str | None = None
    model_used: str | None = None
    safety_flags: int | None = None
    result: Dict[str, Any] | None = None
    user_id: int | None = None
