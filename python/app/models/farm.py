from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from datetime import datetime as _datetime


class Farm(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    name: str
    description: str | None = None
    location_state: str
    location_district: str
    location_block: str | None = None
    location_village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    total_area: float
    cultivable_area: float | None = None
    area_unit: str | None = None
    primary_soil_type: str | None = None
    soil_ph: float | None = None
    soil_characteristics: Dict[str, Any] | None = None
    irrigation_type: str | None = None
    water_availability: str | None = None
    previous_crops: str | None = None
    farming_experience_years: int | None = None
    investment_capacity_per_acre: float | None = None
    farm_profile_embedding: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ph_level: float | None = None
    organic_carbon: float | None = None
    electrical_conductivity: float | None = None
    sulfur: float | None = None
    zinc: float | None = None
    iron: float | None = None
    boron: float | None = None
    copper: float | None = None
    manganese: float | None = None
    soil_depth_class: str | None = None
    slope_class: str | None = None
    erosion_class: str | None = None
    soil_texture_class: str | None = None
    land_capability_class: str | None = None
    land_irrigability_class: str | None = None
    hydrological_soil_group: str | None = None
    shc_data_source: str | None = None
    shc_fetched_at: datetime | None = None
    shc_partial_data: bool | None = None
    shc_unavailable_styles: str | None = None
    user_id: int
    owner_id: int


class FarmInput(BaseModel):
    enable: int | None = None
    name: str | None = None
    description: str | None = None
    location_state: str | None = None
    location_district: str | None = None
    location_block: str | None = None
    location_village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    total_area: float | None = None
    cultivable_area: float | None = None
    area_unit: str | None = None
    primary_soil_type: str | None = None
    soil_ph: float | None = None
    soil_characteristics: Dict[str, Any] | None = None
    irrigation_type: str | None = None
    water_availability: str | None = None
    previous_crops: str | None = None
    farming_experience_years: int | None = None
    investment_capacity_per_acre: float | None = None
    farm_profile_embedding: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ph_level: float | None = None
    organic_carbon: float | None = None
    electrical_conductivity: float | None = None
    sulfur: float | None = None
    zinc: float | None = None
    iron: float | None = None
    boron: float | None = None
    copper: float | None = None
    manganese: float | None = None
    soil_depth_class: str | None = None
    slope_class: str | None = None
    erosion_class: str | None = None
    soil_texture_class: str | None = None
    land_capability_class: str | None = None
    land_irrigability_class: str | None = None
    hydrological_soil_group: str | None = None
    shc_data_source: str | None = None
    shc_fetched_at: _datetime | None = None
    shc_partial_data: bool | None = None
    shc_unavailable_styles: str | None = None
    user_id: int | None = None
    owner_id: int | None = None
