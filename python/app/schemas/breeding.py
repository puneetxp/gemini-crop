"""
Breeding Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.types import JsonDecimal

# ============================================================================
# Breeding Record Schemas
# ============================================================================


class BreedingRecordBase(BaseModel):
    """Base breeding record schema"""

    livestock_id: int = Field(..., description="Parent livestock ID")
    farmer_id: int = Field(..., description="Farmer/owner ID")
    breeding_type: str = Field(..., description="Breeding type: natural, artificial_insemination")
    breeding_date: date = Field(..., description="Date of breeding")
    mate_id: Optional[int] = Field(None, description="Mate livestock ID if known")
    mate_breed: Optional[str] = Field(None, description="Mate breed if external")
    expected_delivery_date: Optional[date] = Field(
        None, description="Expected calving/kidding date"
    )
    pregnancy_status: str = Field(
        default="pending", description="Status: pending, confirmed, delivered, failed"
    )
    breeding_cost: Optional[JsonDecimal] = Field(
        None, ge=0, description="Cost of breeding service in INR"
    )
    veterinarian_name: Optional[str] = Field(None, description="Veterinarian name")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("breeding_type")
    @classmethod
    def validate_breeding_type(cls, v: str) -> str:
        """Validate breeding type"""
        allowed = ["natural", "artificial_insemination"]
        if v.lower() not in allowed:
            raise ValueError(f"Breeding type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("pregnancy_status")
    @classmethod
    def validate_pregnancy_status(cls, v: str) -> str:
        """Validate pregnancy status"""
        allowed = ["pending", "confirmed", "delivered", "failed"]
        if v.lower() not in allowed:
            raise ValueError(f"Pregnancy status must be one of: {', '.join(allowed)}")
        return v.lower()


class BreedingRecordCreate(BreedingRecordBase):
    """Schema for creating breeding record"""

    pass


class BreedingRecordUpdate(BaseModel):
    """Schema for updating breeding record"""

    breeding_type: Optional[str] = None
    breeding_date: Optional[date] = None
    mate_id: Optional[int] = None
    mate_breed: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    pregnancy_status: Optional[str] = None
    number_of_offspring: Optional[int] = Field(None, ge=0)
    breeding_cost: Optional[JsonDecimal] = Field(None, ge=0)
    veterinarian_name: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("breeding_type")
    @classmethod
    def validate_breeding_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate breeding type if provided"""
        if v is None:
            return v
        allowed = ["natural", "artificial_insemination"]
        if v.lower() not in allowed:
            raise ValueError(f"Breeding type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("pregnancy_status")
    @classmethod
    def validate_pregnancy_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate pregnancy status if provided"""
        if v is None:
            return v
        allowed = ["pending", "confirmed", "delivered", "failed"]
        if v.lower() not in allowed:
            raise ValueError(f"Pregnancy status must be one of: {', '.join(allowed)}")
        return v.lower()


class BreedingRecordResponse(BreedingRecordBase):
    """Schema for breeding record response"""

    id: int
    actual_delivery_date: Optional[date] = None
    number_of_offspring: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    class Config:
        from_attributes = True


# ============================================================================
# Offspring Schemas
# ============================================================================


class OffspringBase(BaseModel):
    """Base offspring schema"""

    breeding_record_id: int = Field(..., description="Breeding record ID")
    farmer_id: int = Field(..., description="Farmer/owner ID")
    birth_date: date = Field(..., description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender: male, female")
    birth_weight: Optional[JsonDecimal] = Field(None, ge=0, description="Birth weight in kg")
    health_status: str = Field(default="healthy", description="Status: healthy, weak, deceased")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender if provided"""
        if v is None:
            return v
        allowed = ["male", "female"]
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("health_status")
    @classmethod
    def validate_health_status(cls, v: str) -> str:
        """Validate health status"""
        allowed = ["healthy", "weak", "deceased"]
        if v.lower() not in allowed:
            raise ValueError(f"Health status must be one of: {', '.join(allowed)}")
        return v.lower()


class OffspringCreate(OffspringBase):
    """Schema for creating offspring"""

    pass


class OffspringUpdate(BaseModel):
    """Schema for updating offspring"""

    livestock_id: Optional[int] = None
    gender: Optional[str] = None
    birth_weight: Optional[JsonDecimal] = Field(None, ge=0)
    health_status: Optional[str] = None
    current_weight: Optional[JsonDecimal] = Field(None, ge=0)
    growth_rate: Optional[JsonDecimal] = Field(None, ge=0)
    weaning_date: Optional[date] = None
    sale_date: Optional[date] = None
    sale_price: Optional[JsonDecimal] = Field(None, ge=0)
    notes: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender if provided"""
        if v is None:
            return v
        allowed = ["male", "female"]
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("health_status")
    @classmethod
    def validate_health_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate health status if provided"""
        if v is None:
            return v
        allowed = ["healthy", "weak", "deceased"]
        if v.lower() not in allowed:
            raise ValueError(f"Health status must be one of: {', '.join(allowed)}")
        return v.lower()


class OffspringResponse(OffspringBase):
    """Schema for offspring response"""

    id: int
    livestock_id: Optional[int] = None
    current_weight: Optional[JsonDecimal] = None
    growth_rate: Optional[JsonDecimal] = None
    weaning_date: Optional[date] = None
    sale_date: Optional[date] = None
    sale_price: Optional[JsonDecimal] = None
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    class Config:
        from_attributes = True


# ============================================================================
# Breeding Recommendation Schemas
# ============================================================================


class BreedingRecommendationRequest(BaseModel):
    """Request schema for breeding recommendations"""

    livestock_id: int = Field(..., description="Livestock ID to get breeding recommendations for")


class BreedingPairRecommendation(BaseModel):
    """Schema for breeding pair recommendation"""

    mate_id: Optional[int] = Field(None, description="Recommended mate livestock ID")
    mate_breed: str = Field(..., description="Recommended mate breed")
    compatibility_score: JsonDecimal = Field(
        ..., ge=0, le=1, description="Compatibility score (0-1)"
    )
    expected_offspring_traits: dict = Field(..., description="Expected offspring characteristics")
    reasoning: str = Field(..., description="Reasoning for recommendation")


class BreedingRecommendationResponse(BaseModel):
    """Response schema for breeding recommendations"""

    livestock_id: int
    livestock_breed: str
    livestock_species: str
    recommendations: List[BreedingPairRecommendation]
    optimal_breeding_season: str
    estimated_gestation_days: int
    breeding_tips: List[str]


# ============================================================================
# Breeding Program Report Schemas
# ============================================================================


class BreedingProgramReportRequest(BaseModel):
    """Request schema for breeding program report"""

    farmer_id: int = Field(..., description="Farmer ID")
    start_date: Optional[date] = Field(None, description="Report start date")
    end_date: Optional[date] = Field(None, description="Report end date")


class BreedingProgramMetrics(BaseModel):
    """Breeding program metrics"""

    total_breedings: int
    successful_breedings: int
    success_rate: JsonDecimal
    total_offspring: int
    average_offspring_per_breeding: JsonDecimal
    total_breeding_cost: JsonDecimal
    total_offspring_revenue: JsonDecimal
    breeding_roi: JsonDecimal
    genetic_improvement_score: JsonDecimal


class BreedingProgramReportResponse(BaseModel):
    """Response schema for breeding program report"""

    farmer_id: int
    report_period: dict
    metrics: BreedingProgramMetrics
    breeding_records: List[BreedingRecordResponse]
    offspring_summary: dict
    genetic_trends: dict
    recommendations: List[str]
