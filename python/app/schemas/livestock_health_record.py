"""
Livestock Health Record Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.types import JsonDecimal


class LivestockHealthRecordBase(BaseModel):
    """Base health record schema with common fields"""

    livestock_id: int = Field(..., description="Livestock ID")
    record_type: str = Field(
        ..., description="Type: vaccination, checkup, treatment, breeding, observation"
    )
    record_date: date = Field(..., description="Date of record")
    description: str = Field(..., description="Detailed description of the record")
    veterinarian_name: Optional[str] = Field(None, description="Veterinarian name if applicable")
    cost: Optional[JsonDecimal] = Field(None, ge=0, description="Cost in INR")
    next_due_date: Optional[date] = Field(
        None, description="Next due date for vaccinations/checkups"
    )
    notes: Optional[str] = Field(None, description="Additional notes")

    # Additional fields for specific record types
    medication_name: Optional[str] = Field(None, description="Medication name for treatments")
    dosage: Optional[str] = Field(None, description="Dosage information")
    treatment_outcome: Optional[str] = Field(
        None, description="Outcome: recovered, ongoing, deceased"
    )

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        """Validate record type is one of allowed values"""
        allowed = ["vaccination", "checkup", "treatment", "breeding", "observation"]
        if v.lower() not in allowed:
            raise ValueError(f"Record type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("treatment_outcome")
    @classmethod
    def validate_treatment_outcome(cls, v: Optional[str]) -> Optional[str]:
        """Validate treatment outcome if provided"""
        if v is None:
            return v
        allowed = ["recovered", "ongoing", "deceased", "improved", "no_change"]
        if v.lower() not in allowed:
            raise ValueError(f"Treatment outcome must be one of: {', '.join(allowed)}")
        return v.lower()


class HealthRecordCreate(LivestockHealthRecordBase):
    """Schema for creating new health record"""

    pass


class HealthRecordUpdate(BaseModel):
    """Schema for updating health record"""

    record_type: Optional[str] = None
    record_date: Optional[date] = None
    description: Optional[str] = None
    veterinarian_name: Optional[str] = None
    cost: Optional[JsonDecimal] = Field(None, ge=0)
    next_due_date: Optional[date] = None
    notes: Optional[str] = None
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    treatment_outcome: Optional[str] = None

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate record type if provided"""
        if v is None:
            return v
        allowed = ["vaccination", "checkup", "treatment", "breeding", "observation"]
        if v.lower() not in allowed:
            raise ValueError(f"Record type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("treatment_outcome")
    @classmethod
    def validate_treatment_outcome(cls, v: Optional[str]) -> Optional[str]:
        """Validate treatment outcome if provided"""
        if v is None:
            return v
        allowed = ["recovered", "ongoing", "deceased", "improved", "no_change"]
        if v.lower() not in allowed:
            raise ValueError(f"Treatment outcome must be one of: {', '.join(allowed)}")
        return v.lower()


class HealthRecordResponse(LivestockHealthRecordBase):
    """Schema for health record response"""

    id: int
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    class Config:
        from_attributes = True


class VaccinationSchedule(BaseModel):
    """Schema for vaccination schedule"""

    livestock_id: int
    species: str
    age_months: int
    upcoming_vaccinations: list[dict] = Field(
        default_factory=list, description="List of upcoming vaccinations"
    )
    completed_vaccinations: list[dict] = Field(
        default_factory=list, description="List of completed vaccinations"
    )
    overdue_vaccinations: list[dict] = Field(
        default_factory=list, description="List of overdue vaccinations"
    )


class HealthRecordReport(BaseModel):
    """Schema for comprehensive health record report"""

    livestock_id: int
    species: str
    breed: str
    total_records: int
    vaccinations: list[HealthRecordResponse] = Field(default_factory=list)
    treatments: list[HealthRecordResponse] = Field(default_factory=list)
    checkups: list[HealthRecordResponse] = Field(default_factory=list)
    observations: list[HealthRecordResponse] = Field(default_factory=list)
    total_health_cost: JsonDecimal = Field(default=Decimal("0"), description="Total health costs")
    last_checkup_date: Optional[date] = None
    upcoming_vaccinations: list[dict] = Field(default_factory=list)
    health_summary: str = Field(default="", description="Summary of health status")
