from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class AnnualStrategy(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    year: int
    kharif_crop: str | None = None
    kharif_profit_estimate: float | None = None
    kharif_confidence_score: float | None = None
    rabi_crop: str | None = None
    rabi_profit_estimate: float | None = None
    rabi_confidence_score: float | None = None
    zaid_crop: str | None = None
    zaid_profit_estimate: float | None = None
    zaid_confidence_score: float | None = None
    total_annual_profit: float | None = None
    implementation_timeline: str | None = None
    alternative_options: str | None = None
    risk_mitigation: str | None = None
    bedrock_response: str | None = None
    status: str | None = None
    farm_id: int
    farmer_id: int


class AnnualStrategyInput(BaseModel):
    enable: int | None = None
    year: int | None = None
    kharif_crop: str | None = None
    kharif_profit_estimate: float | None = None
    kharif_confidence_score: float | None = None
    rabi_crop: str | None = None
    rabi_profit_estimate: float | None = None
    rabi_confidence_score: float | None = None
    zaid_crop: str | None = None
    zaid_profit_estimate: float | None = None
    zaid_confidence_score: float | None = None
    total_annual_profit: float | None = None
    implementation_timeline: str | None = None
    alternative_options: str | None = None
    risk_mitigation: str | None = None
    bedrock_response: str | None = None
    status: str | None = None
    farm_id: int | None = None
    farmer_id: int | None = None
