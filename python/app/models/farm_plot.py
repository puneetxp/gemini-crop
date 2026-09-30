from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class FarmPlot(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    plot_name: str
    area: float
    soil_type: str
    irrigation_type: str
    state: str
    district: str
    previous_crops: str | None = None
    investment_capacity: float | None = None
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
    farm_id: int


class FarmPlotInput(BaseModel):
    enable: int | None = None
    plot_name: str | None = None
    area: float | None = None
    soil_type: str | None = None
    irrigation_type: str | None = None
    state: str | None = None
    district: str | None = None
    previous_crops: str | None = None
    investment_capacity: float | None = None
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
    farm_id: int | None = None
