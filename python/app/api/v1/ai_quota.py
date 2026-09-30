"""
AI Usage Quota API Endpoints

Provides endpoints for checking and managing AI usage quotas.
"""

import logging
from datetime import date, datetime
from typing import Annotated, Union

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import AIQuotaSvc
from app.schemas.ai_quota import (
    QuotaCheckResponse,
    QuotaIncrementRequest,
    QuotaResetResponse,
    QuotaStatusResponse,
)
from app.services.ai_quota_service import AIQuotaService

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user, get_current_admin

router = APIRouter(
    prefix="/ai-quota", tags=["ai-quota"], dependencies=[Depends(get_current_active_user)]
)


def _ensure_self(user_id: int, current_user) -> None:
    """Users may only see or spend their own quota; admins may act for anyone."""
    if current_user.id != user_id and getattr(current_user, "user_type", None) != "admin":
        raise HTTPException(status_code=403, detail="You can only access your own quota")


# Removed helper-function dependency injection to enable direct cmd+click to class definition


@router.get("/status/{user_id}", response_model=QuotaStatusResponse)
async def get_quota_status(
    user_id: int,
    service: AIQuotaSvc,
    current_user=Depends(get_current_active_user),
):
    """
    Get current AI usage quota status for user

    Returns:
    - GPS-enhanced requests used today
    - Pincode-based requests used today
    - Remaining GPS-enhanced quota
    - Next quota reset time

    - **user_id**: User ID to check quota for (integer from users.id)
    """
    _ensure_self(user_id, current_user)
    try:
        quota_status = await service.get_quota_status(user_id)
        return quota_status
    except Exception as e:
        logger.error(f"Error getting quota status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota status",
        )


@router.post("/check", response_model=QuotaCheckResponse)
async def check_quota(
    user_id: int,
    service: AIQuotaSvc,
    has_gps: bool = False,
    current_user=Depends(get_current_active_user),
):
    """
    Check if user can make AI request

    Checks quota availability before making Bedrock API call.

    - **user_id**: User ID (integer from users.id)
    - **has_gps**: Whether request includes GPS coordinates

    Returns whether GPS-enhanced request is allowed and remaining quota.
    """
    _ensure_self(user_id, current_user)
    try:
        check_result = await service.check_quota(user_id, has_gps)
        return check_result
    except Exception as e:
        logger.error(f"Error checking quota for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check quota"
        )


@router.post("/increment", response_model=QuotaStatusResponse)
async def increment_usage(
    request: QuotaIncrementRequest,
    service: AIQuotaSvc,
    current_user=Depends(get_current_active_user),
):
    """
    Increment AI usage counter

    Called after successful Bedrock API call to track usage.

    - **user_id**: User ID (integer from users.id)
    - **is_gps_enhanced**: Whether this was a GPS-enhanced request

    Returns updated quota status.
    """
    _ensure_self(request.user_id, current_user)
    try:
        quota_status = await service.increment_usage(request.user_id, request.is_gps_enhanced)
        return quota_status
    except Exception as e:
        logger.error(f"Error incrementing usage for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment usage"
        )


@router.post("/reset", response_model=QuotaResetResponse)
async def reset_daily_quota(
    service: AIQuotaSvc,
    current_user=Depends(get_current_admin),
):
    """
    Reset daily quota for all users

    Called by scheduled job at midnight IST.
    Resets GPS-enhanced and pincode request counters to 0.

    **Admin only** - Should be protected by authentication.

    Returns number of users reset.
    """
    try:
        result = await service.reset_daily_quota()
        return result
    except Exception as e:
        logger.error(f"Error resetting daily quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset quota"
        )


@router.put("/limit/{user_id}", response_model=QuotaStatusResponse)
async def update_quota_limit(
    user_id: int,
    new_limit: int,
    service: AIQuotaSvc,
    current_user=Depends(get_current_admin),
):
    """
    Update quota limit for specific user

    **Admin only** - Should be protected by authentication.

    Allows setting custom quota limits for premium users or testing.

    - **user_id**: User ID (integer from users.id)
    - **new_limit**: New daily GPS-enhanced request limit

    Returns updated quota status.
    """
    if new_limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Quota limit must be at least 1"
        )

    try:
        quota_status = await service.update_quota_limit(user_id, new_limit)
        return quota_status
    except Exception as e:
        logger.error(f"Error updating quota limit for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update quota limit"
        )


@router.get("/statistics", response_model=dict)
async def get_usage_statistics(
    service: AIQuotaSvc,
    start_date: date = None,
    end_date: date = None,
    current_user=Depends(get_current_admin),
):
    """
    Get AI usage statistics for date range

    **Admin only** - Should be protected by authentication.

    Returns aggregated usage statistics including:
    - Total users
    - Total GPS-enhanced requests
    - Total pincode-based requests
    - Average requests per user

    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="End date must be after start date"
        )

    try:
        stats = await service.get_usage_statistics(start_date, end_date)
        return stats
    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )
