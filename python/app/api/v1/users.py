"""
User profile management API endpoints
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, get_current_verified_user, security
from app.core.database import get_db
from app.core.dependencies import DB, AuthCredentials, CurrentUser, VerifiedUser
from app.orm.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    MessageResponse,
    MFAPreferenceRequest,
    UpdateUserAttributesRequest,
)
from app.schemas.user import UserProfileResponse, UserResponse, UserUpdate
from app.services.cognito_service import cognito_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile_alias(current_user: CurrentUser, credentials: AuthCredentials):
    """Registry alias for get profile"""
    return await get_current_user_profile(current_user, credentials)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: CurrentUser, credentials: AuthCredentials):
    """
    Get current user's profile

    Returns detailed user profile including Cognito attributes.
    Requires valid JWT token.
    """
    try:
        # Get additional Cognito attributes
        access_token = credentials.credentials
        cognito_user = cognito_service.get_user(access_token)

        return UserProfileResponse(
            user=UserResponse.from_orm(current_user),
            cognito_attributes=cognito_user.get("attributes", {}),
        )

    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile_alias(
    user_update: UserUpdate, current_user: CurrentUser, credentials: AuthCredentials, db: DB
):
    """Registry alias for update profile"""
    return await update_current_user_profile(user_update, current_user, credentials, db)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate, current_user: CurrentUser, credentials: AuthCredentials, db: DB
):
    """
    Update current user's profile

    - **full_name**: Update full name
    - **email**: Update email (requires verification)
    - **phone_number**: Update phone number (requires verification)
    - **language_preference**: Update preferred language

    Updates both database and Cognito user attributes.
    """
    try:
        access_token = credentials.credentials
        update_data = user_update.dict(exclude_unset=True)

        # Prepare Cognito attributes update
        cognito_attributes = {}
        if "full_name" in update_data:
            cognito_attributes["name"] = update_data["full_name"]
            current_user.full_name = update_data["full_name"]

        if "email" in update_data:
            cognito_attributes["email"] = update_data["email"]
            current_user.email = update_data["email"]
            current_user.is_verified = 0  # Requires re-verification

        if "phone_number" in update_data:
            cognito_attributes["phone_number"] = update_data["phone_number"]
            current_user.phone_number = update_data["phone_number"]
            current_user.is_verified = 0  # Requires re-verification

        if "language_preference" in update_data:
            current_user.language_preference = update_data["language_preference"]

        # Update Cognito attributes if any
        if cognito_attributes:
            cognito_service.update_user_attributes(
                access_token=access_token, attributes=cognito_attributes
            )

        # Update database
        db.commit()
        db.refresh(current_user)

        logger.info(f"User {current_user.username} profile updated")

        return UserResponse.from_orm(current_user)

    except Exception as e:
        logger.error(f"Update profile error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/change-password", response_model=MessageResponse)
async def change_password_alias(
    request: ChangePasswordRequest, credentials: AuthCredentials, current_user: CurrentUser
):
    """Registry alias for change password"""
    return await change_password(request, credentials, current_user)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest, credentials: AuthCredentials, current_user: CurrentUser
):
    """
    Change user password (when logged in)

    - **previous_password**: Current password
    - **proposed_password**: New password (minimum 8 characters)

    Requires valid JWT token and current password.
    """
    try:
        access_token = credentials.credentials

        cognito_service.change_password(
            access_token=access_token,
            previous_password=request.previous_password,
            proposed_password=request.proposed_password,
        )

        logger.info(f"Password changed for user {current_user.username}")

        return MessageResponse(message="Password changed successfully", success=True)

    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/signout", response_model=MessageResponse)
async def sign_out(credentials: AuthCredentials, current_user: CurrentUser):
    """
    Sign out current user

    Invalidates all tokens for the user.
    Requires valid JWT token.
    """
    try:
        access_token = credentials.credentials

        cognito_service.sign_out(access_token)

        logger.info(f"User {current_user.username} signed out")

        return MessageResponse(message="Signed out successfully", success=True)

    except Exception as e:
        logger.error(f"Sign out error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/me/mfa/enable", response_model=MessageResponse)
async def enable_mfa(credentials: AuthCredentials, current_user: CurrentUser):
    """
    Enable SMS-based MFA for current user

    Requires valid JWT token and verified phone number.
    """
    try:
        if not current_user.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number required for MFA"
            )

        access_token = credentials.credentials

        cognito_service.enable_mfa(access_token)

        logger.info(f"MFA enabled for user {current_user.username}")

        return MessageResponse(
            message="MFA enabled successfully. You will receive SMS codes on sign-in.", success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enable MFA error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/me/mfa/disable", response_model=MessageResponse)
async def disable_mfa(credentials: AuthCredentials, current_user: CurrentUser):
    """
    Disable SMS-based MFA for current user

    Requires valid JWT token.
    """
    try:
        access_token = credentials.credentials

        cognito_service.disable_mfa(access_token)

        logger.info(f"MFA disabled for user {current_user.username}")

        return MessageResponse(message="MFA disabled successfully", success=True)

    except Exception as e:
        logger.error(f"Disable MFA error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, current_user: CurrentUser, db: DB):
    """
    Get user by ID

    Returns public user profile information.
    Requires authentication.
    """
    try:
        # Raw SQL via app.core.db.DB (app.orm.user.User is not a SQLAlchemy model)
        from app.core.db import DB as RawDB

        rows = RawDB.raw("SELECT * FROM users WHERE id = ?", [user_id]).result
        user = dict(rows[0]) if rows else None

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.pop("password", None)
        # Public profile: contact details and identity-provider ids only for yourself or an admin.
        if user["id"] != current_user.id and getattr(current_user, "user_type", None) != "admin":
            for private in (
                "email",
                "phone",
                "phone_number",
                "cognito_user_id",
                "firebase_id",
                "google_id",
                "facebook_id",
            ):
                user[private] = None

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user"
        )
