"""
Authentication request/response schemas with enhanced validation and sanitization
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validation import (
    EnumValidator,
    sanitize_input,
    validate_enum,
    validate_phone,
)


class SignUpRequest(BaseModel):
    """User registration request"""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (min 8 characters)"
    )
    email: EmailStr = Field(..., description="Email address")
    phone_number: Optional[str] = Field(None, description="Phone number (+919876543210), optional")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    user_type: str = Field(default="farmer", description="User type: farmer, buyer, admin")

    # Optional address fields
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude (optional)")
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="GPS longitude (optional)"
    )
    pincode: Optional[str] = Field(
        None,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit postal code (optional)",
    )
    state: Optional[str] = Field(
        None, min_length=2, max_length=100, description="State name (optional)"
    )
    district: Optional[str] = Field(
        None, min_length=2, max_length=100, description="District name (optional)"
    )
    village: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Village/VPO name (optional)"
    )
    address_line: Optional[str] = Field(None, max_length=255, description="Address line (optional)")

    @field_validator("username", "full_name")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        """Sanitize text fields"""
        return sanitize_input(v, allow_html=False)

    @field_validator("state", "district", "village", "address_line")
    @classmethod
    def sanitize_address_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize address fields"""
        if v is None:
            return None
        return sanitize_input(v, allow_html=False)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number when given; blank means none"""
        if v is None or not v.strip():
            return None
        return validate_phone(v)

    @field_validator("user_type")
    @classmethod
    def validate_user_type_enum(cls, v: str) -> str:
        """Validate user type"""
        return validate_enum(v, EnumValidator.USER_TYPES, "user_type")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")

        # Check for at least one uppercase, one lowercase, one digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class SignUpResponse(BaseModel):
    """User registration response"""

    user_sub: str = Field(..., description="Cognito user ID")
    user_confirmed: bool = Field(..., description="Whether user is confirmed")
    message: str = Field(..., description="Success message")
    code_delivery_details: Optional[Dict[str, Any]] = Field(
        None, description="Verification code delivery details"
    )


class ConfirmSignUpRequest(BaseModel):
    """Confirm user registration request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username to confirm")
    confirmation_code: str = Field(
        ..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit verification code"
    )

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class ResendCodeRequest(BaseModel):
    """Resend confirmation code request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class SignInRequest(BaseModel):
    """User sign-in request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class GoogleSignInRequest(BaseModel):
    """Sign in with a Firebase ID token (Google, email/password or phone) obtained on the client"""

    id_token: str = Field(..., description="Firebase ID token from the client SDK")
    refresh_token: Optional[str] = Field(
        None, description="Firebase refresh token, used by /auth/refresh"
    )


class SignInResponse(BaseModel):
    """User sign-in response"""

    access_token: str = Field(..., description="JWT access token")
    id_token: str = Field(..., description="JWT ID token")
    refresh_token: str = Field(..., description="Refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")
    user: Optional[Dict[str, Any]] = Field(None, description="User profile data")


class MFAChallengeResponse(BaseModel):
    """MFA challenge response"""

    challenge: str = Field(..., description="Challenge type (SMS_MFA)")
    session: str = Field(..., description="Session token for MFA")
    message: str = Field(..., description="Instructions for user")


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    session: str = Field(..., description="Session token from sign-in")
    mfa_code: str = Field(
        ..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit MFA code"
    )

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    refresh_token: str = Field(..., description="Refresh token")

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)


class ForgotPasswordResponse(BaseModel):
    """Forgot password response"""

    message: str = Field(..., description="Success message")
    code_delivery_details: Optional[Dict[str, Any]] = Field(
        None, description="Code delivery details"
    )


class ConfirmForgotPasswordRequest(BaseModel):
    """Confirm forgot password request"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    confirmation_code: str = Field(
        ..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit verification code"
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (min 8 characters)"
    )

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitize username"""
        return sanitize_input(v, allow_html=False)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")

        # Check for at least one uppercase, one lowercase, one digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class ChangePasswordRequest(BaseModel):
    """Change password request (when logged in)"""

    previous_password: str = Field(
        ..., min_length=8, max_length=128, description="Current password"
    )
    proposed_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (min 8 characters)"
    )

    @field_validator("proposed_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must not exceed 128 characters")

        # Check for at least one uppercase, one lowercase, one digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class UpdateUserAttributesRequest(BaseModel):
    """Update user attributes request"""

    attributes: Dict[str, str] = Field(..., description="Attributes to update")


class MFAPreferenceRequest(BaseModel):
    """MFA preference request"""

    enabled: bool = Field(..., description="Enable or disable MFA")


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")
