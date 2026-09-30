from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class PestDiseaseData(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    name: str
    type: str
    scientific_name: str | None = None
    description: str
    affected_crops: str | None = None
    risk_stages: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    humidity_min: int | None = None
    humidity_max: int | None = None
    rainfall_min: float | None = None
    severity: str
    organic_treatments: str | None = None
    chemical_treatments: str | None = None
    prevention_measures: str | None = None
    timing_instructions: str | None = None
    data_source: str | None = None
    last_updated: datetime | None = None


class PestDiseaseDataInput(BaseModel):
    enable: int | None = None
    name: str | None = None
    type: str | None = None
    scientific_name: str | None = None
    description: str | None = None
    affected_crops: str | None = None
    risk_stages: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    humidity_min: int | None = None
    humidity_max: int | None = None
    rainfall_min: float | None = None
    severity: str | None = None
    organic_treatments: str | None = None
    chemical_treatments: str | None = None
    prevention_measures: str | None = None
    timing_instructions: str | None = None
    data_source: str | None = None
    last_updated: _datetime | None = None
