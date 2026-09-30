"""
Soil health and management schemas
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class SoilTestBase(BaseModel):
    """Base soil test schema"""

    plot_id: int = Field(..., description="Plot ID")
    test_date: date = Field(..., description="Date of soil test")
    ph_level: Optional[float] = Field(None, ge=0, le=14, description="Soil pH level")
    nitrogen_kg_per_acre: Optional[float] = Field(
        None, ge=0, description="Nitrogen content (kg/acre)"
    )
    phosphorus_kg_per_acre: Optional[float] = Field(
        None, ge=0, description="Phosphorus content (kg/acre)"
    )
    potassium_kg_per_acre: Optional[float] = Field(
        None, ge=0, description="Potassium content (kg/acre)"
    )
    organic_carbon_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Organic carbon percentage"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SoilTestCreate(SoilTestBase):
    """Soil test creation schema"""

    pass


class SoilTestUpdate(BaseModel):
    """Soil test update schema"""

    test_date: Optional[date] = None
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    nitrogen_kg_per_acre: Optional[float] = Field(None, ge=0)
    phosphorus_kg_per_acre: Optional[float] = Field(None, ge=0)
    potassium_kg_per_acre: Optional[float] = Field(None, ge=0)
    organic_carbon_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=1000)


class SoilTestResponse(SoilTestBase):
    """Soil test response schema"""

    id: int = Field(..., description="Soil test ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class FertilizerApplicationBase(BaseModel):
    """Base fertilizer application schema"""

    plot_id: int = Field(..., description="Plot ID")
    application_date: date = Field(..., description="Date of application")
    fertilizer_type: str = Field(
        ..., description="Fertilizer type: organic, urea, dap, mop, npk, mixed"
    )
    quantity_kg: float = Field(..., gt=0, description="Quantity applied (kg)")
    cost_inr: Optional[float] = Field(None, ge=0, description="Cost in INR")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    @validator("fertilizer_type")
    def validate_fertilizer_type(cls, v):
        allowed_types = ["organic", "urea", "dap", "mop", "npk", "mixed", "compost", "manure"]
        if v.lower() not in allowed_types:
            raise ValueError(f'fertilizer_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class FertilizerApplicationCreate(FertilizerApplicationBase):
    """Fertilizer application creation schema"""

    pass


class FertilizerApplicationUpdate(BaseModel):
    """Fertilizer application update schema"""

    application_date: Optional[date] = None
    fertilizer_type: Optional[str] = None
    quantity_kg: Optional[float] = Field(None, gt=0)
    cost_inr: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)


class FertilizerApplicationResponse(FertilizerApplicationBase):
    """Fertilizer application response schema"""

    id: int = Field(..., description="Application ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SoilAmendmentBase(BaseModel):
    """Base soil amendment schema"""

    plot_id: int = Field(..., description="Plot ID")
    amendment_date: date = Field(..., description="Date of amendment")
    amendment_type: str = Field(
        ..., description="Amendment type: lime, gypsum, sulfur, compost, biochar"
    )
    quantity_kg: float = Field(..., gt=0, description="Quantity applied (kg)")
    purpose: Optional[str] = Field(None, max_length=500, description="Purpose of amendment")
    cost_inr: Optional[float] = Field(None, ge=0, description="Cost in INR")

    @validator("amendment_type")
    def validate_amendment_type(cls, v):
        allowed_types = ["lime", "gypsum", "sulfur", "compost", "biochar", "other"]
        if v.lower() not in allowed_types:
            raise ValueError(f'amendment_type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class SoilAmendmentCreate(SoilAmendmentBase):
    """Soil amendment creation schema"""

    pass


class SoilAmendmentUpdate(BaseModel):
    """Soil amendment update schema"""

    amendment_date: Optional[date] = None
    amendment_type: Optional[str] = None
    quantity_kg: Optional[float] = Field(None, gt=0)
    purpose: Optional[str] = Field(None, max_length=500)
    cost_inr: Optional[float] = Field(None, ge=0)


class SoilAmendmentResponse(SoilAmendmentBase):
    """Soil amendment response schema"""

    id: int = Field(..., description="Amendment ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SoilHealthSummary(BaseModel):
    """Soil health summary for a plot"""

    plot_id: int
    plot_name: str
    latest_test: Optional[SoilTestResponse] = None
    recent_fertilizer_applications: list[FertilizerApplicationResponse] = []
    recent_amendments: list[SoilAmendmentResponse] = []
    total_fertilizer_cost_last_year: float = 0.0
    soil_health_score: Optional[float] = None  # 0-100 score based on test results
