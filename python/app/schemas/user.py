"""
User profile schemas with enhanced validation and sanitization
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.validation import (
    EnumValidator,
    sanitize_input,
    validate_enum,
    validate_phone,
)


class UserBase(BaseModel):
    """Base user schema"""

    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Email address")
    phone_number: str = Field(..., description="Phone number (+91XXXXXXXXXX)")
    user_type: str = Field(..., description="User type: farmer, buyer, admin")

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        """Sanitize full name to prevent XSS"""
        return sanitize_input(v, allow_html=False)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """Validate and format phone number"""
        return validate_phone(v)

    @field_validator("user_type")
    @classmethod
    def validate_user_type_enum(cls, v: str) -> str:
        """Validate user type is in allowed values"""
        return validate_enum(v, EnumValidator.USER_TYPES, "user_type")


class UserCreate(UserBase):
    """User creation schema"""

    cognito_user_id: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Cognito user ID (sub)"
    )
    firebase_id: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Firebase user ID"
    )
    username: str = Field(..., min_length=3, max_length=50, description="Username")

    @model_validator(mode="before")
    @classmethod
    def set_id_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cog_id = data.get("cognito_user_id")
            fb_id = data.get("firebase_id")

            # Ensure at least one is provided
            if not cog_id and not fb_id:
                raise ValueError("Either cognito_user_id or firebase_id must be provided")
        return data

    @field_validator("cognito_user_id", "firebase_id", "username")
    @classmethod
    def sanitize_ids(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize IDs to prevent injection"""
        if v is None:
            return v
        return sanitize_input(v, allow_html=False)


class UserUpdate(BaseModel):
    """User update schema"""

    full_name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="User's full name"
    )
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone_number: Optional[str] = Field(None, description="Phone number")
    language_preference: Optional[str] = Field(
        None, min_length=2, max_length=10, description="Preferred language"
    )

    @field_validator("full_name", "language_preference")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize string fields"""
        if v is None:
            return v
        return sanitize_input(v, allow_html=False)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return v
        return validate_phone(v)


class UserResponse(UserBase):
    """User response schema"""

    # Phone / Google sign-ups can lack an email or phone; a response must never 500 over that.
    email: Optional[str] = Field(None, description="Email address")
    phone_number: Optional[str] = Field(None, description="Phone number")
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    cognito_user_id: Optional[str] = Field(None, description="Cognito user ID")
    firebase_id: Optional[str] = Field(None, description="Firebase user ID")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email/phone verification status")
    language_preference: Optional[str] = Field(None, description="Preferred language")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @model_validator(mode="before")
    @classmethod
    def map_user_columns(cls, data: Any) -> Any:
        """The users table stores name / phone / preferred_language; the API calls them
        full_name / phone_number / language_preference."""
        if not isinstance(data, dict):
            data = {
                k: getattr(data, k)
                for k in dir(data)
                if not k.startswith("_") and not callable(getattr(data, k, None))
            }
        data = dict(data)
        data.setdefault("full_name", data.get("name") or data.get("username") or "User")
        data.setdefault("phone_number", data.get("phone"))
        data.setdefault("language_preference", data.get("preferred_language"))
        return data

    @field_validator("phone_number")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v) if v else v

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Detailed user profile response"""

    user: UserResponse
    cognito_attributes: dict = Field(..., description="Additional Cognito attributes")
    firebase_attributes: Optional[dict] = Field(None, description="Additional Firebase attributes")

    @model_validator(mode="before")
    @classmethod
    def set_firebase_attributes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cog_attrs = data.get("cognito_attributes")
            fb_attrs = data.get("firebase_attributes")
            if cog_attrs and not fb_attrs:
                data["firebase_attributes"] = cog_attrs
            elif fb_attrs and not cog_attrs:
                data["cognito_attributes"] = fb_attrs
        return data

    class Config:
        from_attributes = True
