"""
Pydantic schemas for market data ingestion
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.types import JsonDecimal


class CropMarketDataCreate(BaseModel):
    """Schema for creating crop market data"""

    # Required fields
    crop_type: str = Field(..., description="Crop type (e.g., Wheat, Rice)")
    state: str = Field(..., description="State name")
    year: int = Field(..., description="Year of data", ge=1900, le=2100)
    avg_price_per_quintal: float = Field(..., description="Average price per quintal", gt=0)

    # Optional fields
    variety: Optional[str] = Field(None, description="Crop variety")
    district: Optional[str] = Field(None, description="District name")
    market_name: Optional[str] = Field(None, description="Market name")
    month: Optional[int] = Field(None, description="Month (1-12)", ge=1, le=12)
    season: Optional[str] = Field(None, description="Season (kharif, rabi, zaid)")

    # Price data
    min_price: Optional[float] = Field(None, description="Minimum price per quintal", gt=0)
    max_price: Optional[float] = Field(None, description="Maximum price per quintal", gt=0)
    modal_price: Optional[float] = Field(None, description="Modal price per quintal", gt=0)

    # Market metrics
    market_demand_score: Optional[float] = Field(
        None, description="Market demand score (0.0-1.0)", ge=0.0, le=1.0
    )
    supply_volume: Optional[float] = Field(None, description="Supply volume", ge=0)
    price_volatility: Optional[float] = Field(None, description="Price volatility percentage", ge=0)

    # Trends
    price_trend: Optional[str] = Field(
        None, description="Price trend (increasing, stable, decreasing)"
    )
    yoy_price_change: Optional[float] = Field(
        None, description="Year-over-year price change percentage"
    )
    mom_price_change: Optional[float] = Field(
        None, description="Month-over-month price change percentage"
    )

    # Data source
    data_source: Optional[str] = Field("manual", description="Data source")
    data_quality_score: Optional[float] = Field(
        0.8, description="Data quality score (0.0-1.0)", ge=0.0, le=1.0
    )

    @validator("season")
    def validate_season(cls, v):
        if v and v.lower() not in ["kharif", "rabi", "zaid"]:
            raise ValueError("Season must be one of: kharif, rabi, zaid")
        return v.lower() if v else v

    @validator("price_trend")
    def validate_price_trend(cls, v):
        if v and v.lower() not in ["increasing", "stable", "decreasing"]:
            raise ValueError("Price trend must be one of: increasing, stable, decreasing")
        return v.lower() if v else v

    class Config:
        json_schema_extra = {
            "example": {
                "crop_type": "Wheat",
                "variety": "HD-2967",
                "state": "Punjab",
                "district": "Ludhiana",
                "market_name": "Ludhiana Mandi",
                "year": 2023,
                "month": 4,
                "season": "rabi",
                "avg_price_per_quintal": 2150.50,
                "min_price": 2000.00,
                "max_price": 2300.00,
                "modal_price": 2150.00,
                "market_demand_score": 0.85,
                "supply_volume": 50000.00,
                "price_volatility": 5.2,
                "price_trend": "increasing",
                "yoy_price_change": 8.5,
                "mom_price_change": 2.3,
                "data_source": "AGMARKNET",
                "data_quality_score": 0.95,
            }
        }


class CropMarketDataResponse(BaseModel):
    """Schema for crop market data response"""

    id: str
    crop_type: str
    variety: Optional[str]
    state: str
    district: Optional[str]
    market_name: Optional[str]
    year: int
    month: Optional[int]
    season: Optional[str]
    avg_price_per_quintal: JsonDecimal
    min_price: Optional[JsonDecimal]
    max_price: Optional[JsonDecimal]
    modal_price: Optional[JsonDecimal]
    market_demand_score: Optional[JsonDecimal]
    supply_volume: Optional[JsonDecimal]
    price_volatility: Optional[JsonDecimal]
    price_trend: Optional[str]
    yoy_price_change: Optional[JsonDecimal]
    mom_price_change: Optional[JsonDecimal]
    data_source: Optional[str]
    data_quality_score: Optional[JsonDecimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkMarketDataCreate(BaseModel):
    """Schema for bulk market data ingestion"""

    data: List[CropMarketDataCreate] = Field(..., description="List of market data records")
    skip_errors: bool = Field(False, description="Skip records with errors and continue")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "crop_type": "Wheat",
                        "state": "Punjab",
                        "year": 2023,
                        "month": 4,
                        "avg_price_per_quintal": 2150.50,
                    },
                    {
                        "crop_type": "Rice",
                        "state": "Punjab",
                        "year": 2023,
                        "month": 10,
                        "avg_price_per_quintal": 2800.00,
                    },
                ],
                "skip_errors": False,
            }
        }


class BulkIngestionResponse(BaseModel):
    """Schema for bulk ingestion response"""

    success_count: int = Field(..., description="Number of successfully ingested records")
    error_count: int = Field(..., description="Number of records with errors")
    total_records: int = Field(..., description="Total number of records processed")
    errors: List[Dict[str, Any]] = Field(..., description="List of errors encountered")

    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 98,
                "error_count": 2,
                "total_records": 100,
                "errors": [
                    {
                        "index": 5,
                        "data": {"crop_type": "Wheat", "state": "Punjab"},
                        "error": "Missing required field: year",
                    }
                ],
            }
        }


class HistoricalYieldCreate(BaseModel):
    """Schema for creating historical yield data"""

    # Required fields
    crop_type: str = Field(..., description="Crop type")
    state: str = Field(..., description="State name")
    year: int = Field(..., description="Year of data", ge=1900, le=2100)
    avg_yield_per_acre: float = Field(..., description="Average yield per acre in quintals", gt=0)

    # Optional fields
    variety: Optional[str] = Field(None, description="Crop variety")
    district: Optional[str] = Field(None, description="District name")
    block: Optional[str] = Field(None, description="Block name")
    season: Optional[str] = Field(None, description="Season (kharif, rabi, zaid)")

    # Yield data
    min_yield: Optional[float] = Field(None, description="Minimum yield per acre", gt=0)
    max_yield: Optional[float] = Field(None, description="Maximum yield per acre", gt=0)

    # Success metrics
    success_rate: Optional[float] = Field(None, description="Success rate percentage", ge=0, le=100)
    farmer_count: Optional[int] = Field(None, description="Number of farmers", ge=0)
    total_area_cultivated: Optional[float] = Field(None, description="Total area in acres", ge=0)

    # Growing conditions
    soil_types: Optional[List[str]] = Field(None, description="Soil types used")
    irrigation_methods: Optional[List[str]] = Field(None, description="Irrigation methods")
    avg_rainfall: Optional[float] = Field(None, description="Average rainfall in mm", ge=0)
    avg_temperature: Optional[float] = Field(None, description="Average temperature in celsius")

    # Quality metrics
    quality_distribution: Optional[Dict[str, float]] = Field(
        None, description="Quality grade distribution"
    )
    avg_quality_grade: Optional[str] = Field(None, description="Average quality grade")

    # Data source
    data_source: Optional[str] = Field("manual", description="Data source")
    data_quality_score: Optional[float] = Field(
        0.8, description="Data quality score", ge=0.0, le=1.0
    )

    @validator("season")
    def validate_season(cls, v):
        if v and v.lower() not in ["kharif", "rabi", "zaid"]:
            raise ValueError("Season must be one of: kharif, rabi, zaid")
        return v.lower() if v else v


class CropProfitabilityCreate(BaseModel):
    """Schema for creating crop profitability data"""

    # Required fields
    crop_type: str = Field(..., description="Crop type")
    state: str = Field(..., description="State name")
    year: int = Field(..., description="Year of data", ge=1900, le=2100)
    avg_profit_per_acre: float = Field(..., description="Average profit per acre")

    # Optional fields
    variety: Optional[str] = Field(None, description="Crop variety")
    district: Optional[str] = Field(None, description="District name")
    season: Optional[str] = Field(None, description="Season (kharif, rabi, zaid)")

    # Profitability metrics
    min_profit_per_acre: Optional[float] = Field(None, description="Minimum profit per acre")
    max_profit_per_acre: Optional[float] = Field(None, description="Maximum profit per acre")

    # Cost breakdown
    seed_cost: Optional[float] = Field(None, description="Seed cost per acre", ge=0)
    fertilizer_cost: Optional[float] = Field(None, description="Fertilizer cost per acre", ge=0)
    pesticide_cost: Optional[float] = Field(None, description="Pesticide cost per acre", ge=0)
    labor_cost: Optional[float] = Field(None, description="Labor cost per acre", ge=0)
    irrigation_cost: Optional[float] = Field(None, description="Irrigation cost per acre", ge=0)
    equipment_cost: Optional[float] = Field(None, description="Equipment cost per acre", ge=0)
    other_costs: Optional[float] = Field(None, description="Other costs per acre", ge=0)
    total_investment_cost: Optional[float] = Field(
        None, description="Total investment per acre", ge=0
    )

    # Revenue
    avg_revenue_per_acre: Optional[float] = Field(
        None, description="Average revenue per acre", ge=0
    )

    # ROI metrics
    roi_percentage: Optional[float] = Field(None, description="ROI percentage")
    break_even_yield: Optional[float] = Field(None, description="Break-even yield", ge=0)
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")

    # Risk assessment
    risk_level: Optional[str] = Field(None, description="Risk level (low, medium, high)")
    price_risk_score: Optional[float] = Field(None, description="Price risk score", ge=0.0, le=1.0)
    yield_risk_score: Optional[float] = Field(None, description="Yield risk score", ge=0.0, le=1.0)

    # Market factors
    market_demand: Optional[str] = Field(None, description="Market demand (low, medium, high)")
    competition_level: Optional[str] = Field(None, description="Competition level")

    # Data source
    data_source: Optional[str] = Field("manual", description="Data source")
    sample_size: Optional[int] = Field(None, description="Sample size", ge=0)

    @validator("season")
    def validate_season(cls, v):
        if v and v.lower() not in ["kharif", "rabi", "zaid"]:
            raise ValueError("Season must be one of: kharif, rabi, zaid")
        return v.lower() if v else v

    @validator("risk_level")
    def validate_risk_level(cls, v):
        if v and v.lower() not in ["low", "medium", "high"]:
            raise ValueError("Risk level must be one of: low, medium, high")
        return v.lower() if v else v


class MarketDataSummary(BaseModel):
    """Schema for market data summary statistics"""

    total_records: int = Field(..., description="Total number of records")
    unique_crops: int = Field(..., description="Number of unique crops")
    unique_states: int = Field(..., description="Number of unique states")
    year_range: Optional[Dict[str, int]] = Field(None, description="Year range (min, max)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_records": 5000,
                "unique_crops": 25,
                "unique_states": 15,
                "year_range": {"min": 2018, "max": 2023},
            }
        }
