from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class SoilTestResult(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    test_date: datetime
    lab_name: str | None = None
    lab_reference_number: str | None = None
    nitrogen_kg_per_ha: float | None = None
    phosphorus_kg_per_ha: float | None = None
    potassium_kg_per_ha: float | None = None
    ph_level: float | None = None
    organic_carbon_percent: float | None = None
    organic_matter_percent: float | None = None
    electrical_conductivity: float | None = None
    sulfur_ppm: float | None = None
    zinc_ppm: float | None = None
    iron_ppm: float | None = None
    manganese_ppm: float | None = None
    copper_ppm: float | None = None
    boron_ppm: float | None = None
    soil_health_score: float | None = None
    test_method: str | None = None
    raw_data_json: str | None = None
    recommendations: str | None = None
    notes: str | None = None
    farm_id: int
    plot_id: int | None = None


class SoilTestResultInput(BaseModel):
    enable: int | None = None
    test_date: _datetime | None = None
    lab_name: str | None = None
    lab_reference_number: str | None = None
    nitrogen_kg_per_ha: float | None = None
    phosphorus_kg_per_ha: float | None = None
    potassium_kg_per_ha: float | None = None
    ph_level: float | None = None
    organic_carbon_percent: float | None = None
    organic_matter_percent: float | None = None
    electrical_conductivity: float | None = None
    sulfur_ppm: float | None = None
    zinc_ppm: float | None = None
    iron_ppm: float | None = None
    manganese_ppm: float | None = None
    copper_ppm: float | None = None
    boron_ppm: float | None = None
    soil_health_score: float | None = None
    test_method: str | None = None
    raw_data_json: str | None = None
    recommendations: str | None = None
    notes: str | None = None
    farm_id: int | None = None
    plot_id: int | None = None
