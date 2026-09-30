from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class SoilTest(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    test_date: date
    test_type: str | None = None
    testing_lab: str | None = None
    lab_report_url: str | None = None
    soil_type: str | None = None
    soil_texture: str | None = None
    soil_color: str | None = None
    ph_level: float
    electrical_conductivity: float | None = None
    organic_carbon: float | None = None
    organic_matter: float | None = None
    nitrogen_n: float | None = None
    phosphorus_p: float | None = None
    potassium_k: float | None = None
    calcium_ca: float | None = None
    magnesium_mg: float | None = None
    sulfur_s: float | None = None
    iron_fe: float | None = None
    manganese_mn: float | None = None
    zinc_zn: float | None = None
    copper_cu: float | None = None
    boron_b: float | None = None
    molybdenum_mo: float | None = None
    nitrogen_status: str | None = None
    phosphorus_status: str | None = None
    potassium_status: str | None = None
    water_holding_capacity: float | None = None
    drainage_quality: str | None = None
    bulk_density: float | None = None
    porosity: float | None = None
    microbial_activity: str | None = None
    earthworm_count: int | None = None
    overall_health_score: float | None = None
    fertility_rating: str | None = None
    lab_recommendations: str | None = None
    fertilizer_recommendations: Dict[str, Any] | None = None
    amendment_recommendations: Dict[str, Any] | None = None
    test_cost: float | None = None
    plot_id: int


class SoilTestInput(BaseModel):
    enable: int | None = None
    test_date: _date | None = None
    test_type: str | None = None
    testing_lab: str | None = None
    lab_report_url: str | None = None
    soil_type: str | None = None
    soil_texture: str | None = None
    soil_color: str | None = None
    ph_level: float | None = None
    electrical_conductivity: float | None = None
    organic_carbon: float | None = None
    organic_matter: float | None = None
    nitrogen_n: float | None = None
    phosphorus_p: float | None = None
    potassium_k: float | None = None
    calcium_ca: float | None = None
    magnesium_mg: float | None = None
    sulfur_s: float | None = None
    iron_fe: float | None = None
    manganese_mn: float | None = None
    zinc_zn: float | None = None
    copper_cu: float | None = None
    boron_b: float | None = None
    molybdenum_mo: float | None = None
    nitrogen_status: str | None = None
    phosphorus_status: str | None = None
    potassium_status: str | None = None
    water_holding_capacity: float | None = None
    drainage_quality: str | None = None
    bulk_density: float | None = None
    porosity: float | None = None
    microbial_activity: str | None = None
    earthworm_count: int | None = None
    overall_health_score: float | None = None
    fertility_rating: str | None = None
    lab_recommendations: str | None = None
    fertilizer_recommendations: Dict[str, Any] | None = None
    amendment_recommendations: Dict[str, Any] | None = None
    test_cost: float | None = None
    plot_id: int | None = None
