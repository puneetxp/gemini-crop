"""
AI Usage Quota Schemas

Pydantic models for AI usage tracking and quota management.
"""

from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AIQuotaBase(BaseModel):
    """Base AI quota model"""

    user_id: int = Field(..., description="User ID")
    date: date_type = Field(..., description="Date for quota tracking")
    gps_enhanced_requests: int = Field(0, ge=0, description="GPS-enhanced Bedrock API calls count")
    pincode_requests: int = Field(0, ge=0, description="Pincode-based recommendations count")
    quota_limit: int = Field(20, ge=1, description="Daily GPS-enhanced request limit")


class AIQuotaCreate(BaseModel):
    """Create AI quota record"""

    user_id: int
    date: date_type
    quota_limit: int = 20


class AIQuotaResponse(AIQuotaBase):
    """AI quota response with metadata"""

    id: int
    last_reset: datetime
    remaining_quota: int = Field(..., description="Remaining GPS-enhanced requests for today")
    quota_exceeded: bool = Field(..., description="Whether quota has been exceeded")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotaStatusResponse(BaseModel):
    """Current quota status for user"""

    user_id: int
    date: date_type
    gps_enhanced_requests: int = Field(..., description="GPS-enhanced requests used today")
    pincode_requests: int = Field(..., description="Pincode-based requests used today")
    quota_limit: int = Field(..., description="Daily GPS-enhanced request limit")
    remaining_quota: int = Field(..., description="Remaining GPS-enhanced requests")
    quota_exceeded: bool = Field(..., description="Whether quota has been exceeded")
    next_reset: datetime = Field(..., description="Next quota reset time (midnight IST)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123,
                "date": "2026-02-28",
                "gps_enhanced_requests": 15,
                "pincode_requests": 42,
                "quota_limit": 20,
                "remaining_quota": 5,
                "quota_exceeded": False,
                "next_reset": "2026-03-01T00:00:00+05:30",
            }
        }
    )


class QuotaIncrementRequest(BaseModel):
    """Request to increment quota usage"""

    user_id: int
    is_gps_enhanced: bool = Field(..., description="Whether this is a GPS-enhanced request")


class QuotaCheckResponse(BaseModel):
    """Response for quota check before AI request"""

    can_use_gps: bool = Field(..., description="Whether GPS-enhanced request is allowed")
    remaining_quota: int = Field(..., description="Remaining GPS-enhanced requests")
    fallback_to_pincode: bool = Field(..., description="Whether to fallback to pincode-based")
    message: str = Field(..., description="User-friendly message about quota status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "can_use_gps": True,
                "remaining_quota": 5,
                "fallback_to_pincode": False,
                "message": "You have 5 GPS-enhanced recommendations remaining today.",
            }
        }
    )


class QuotaResetResponse(BaseModel):
    """Response after quota reset"""

    users_reset: int = Field(..., description="Number of users whose quota was reset")
    reset_time: datetime = Field(..., description="Time of reset")
    message: str = Field(..., description="Reset status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users_reset": 1523,
                "reset_time": "2026-03-01T00:00:00+05:30",
                "message": "Successfully reset quota for 1523 users",
            }
        }
    )
