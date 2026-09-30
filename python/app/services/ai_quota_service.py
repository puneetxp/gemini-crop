"""
AI Usage Quota Service

Manages daily AI usage quotas for GPS-enhanced Bedrock API calls.
Implements 20 GPS-enhanced requests per user per day with unlimited
pincode-based recommendations.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Union
from uuid import UUID

import pytz

from app.orm.ai_usage_quota import AiUsageQuota
from app.schemas.ai_quota import (
    QuotaCheckResponse,
    QuotaIncrementRequest,
    QuotaResetResponse,
    QuotaStatusResponse,
)

logger = logging.getLogger(__name__)


class AIQuotaService:
    """Service for AI usage quota management"""

    DEFAULT_QUOTA_LIMIT = 20
    IST_TIMEZONE = pytz.timezone("Asia/Kolkata")

    def __init__(self, db=None):
        """
        Initialize AI quota service

        Args:
            db: Database session (not used with custom ORM, kept for compatibility)
        """
        self.model = AiUsageQuota

    def get_or_create_quota(self, user_id: Union[int, str], today: Optional[date] = None) -> dict:
        """
        Get or create quota record for user and date

        Args:
            user_id: User ID (integer from users.id)
            today: Date for quota (defaults to today in IST)

        Returns:
            AIUsageQuota record as dictionary
        """
        # Convert to int if string
        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        if today is None:
            today = datetime.now(self.IST_TIMEZONE).date()

        # Try to get existing quota - use and_where_custom for multiple conditions
        quota_model = (
            self.model()
            .and_where_custom([["user_id", "=", user_id_int], ["date", "=", str(today)]])
            .first()
        )

        if quota_model:
            return quota_model.items

        # Create new quota record
        quota_data = {
            "user_id": user_id_int,
            "date": today,
            "gps_enhanced_requests": 0,
            "pincode_requests": 0,
            "quota_limit": self.DEFAULT_QUOTA_LIMIT,
            "last_reset": datetime.now(self.IST_TIMEZONE),
        }

        quota_model = self.model().create(quota_data)
        logger.info(f"Created new quota record for user {user_id_int} on {today}")

        # Return the created record
        created = (
            self.model()
            .and_where_custom([["user_id", "=", user_id_int], ["date", "=", str(today)]])
            .first()
        )
        return created.items if created else quota_data

    async def check_quota(
        self, user_id: Union[int, str], has_gps: bool = False
    ) -> QuotaCheckResponse:
        """
        Check if user can make AI request

        Args:
            user_id: User ID (integer from users.id)
            has_gps: Whether request includes GPS coordinates

        Returns:
            QuotaCheckResponse with availability and message
        """
        quota = self.get_or_create_quota(user_id)

        remaining = quota["quota_limit"] - quota["gps_enhanced_requests"]

        # If no GPS requested, always allow (pincode-based is unlimited)
        if not has_gps:
            return QuotaCheckResponse(
                can_use_gps=False,
                remaining_quota=remaining,
                fallback_to_pincode=False,
                message="Using pincode-based recommendation (unlimited).",
            )

        # GPS requested - check quota
        if remaining > 0:
            return QuotaCheckResponse(
                can_use_gps=True,
                remaining_quota=remaining,
                fallback_to_pincode=False,
                message=f"You have {remaining} GPS-enhanced recommendations remaining today.",
            )
        else:
            return QuotaCheckResponse(
                can_use_gps=False,
                remaining_quota=0,
                fallback_to_pincode=True,
                message="Daily GPS-enhanced quota exceeded. Using pincode-based recommendation instead.",
            )

    async def increment_usage(
        self, user_id: Union[int, str], is_gps_enhanced: bool
    ) -> QuotaStatusResponse:
        """
        Increment usage counter for user

        Args:
            user_id: User ID (integer from users.id)
            is_gps_enhanced: Whether this was a GPS-enhanced request

        Returns:
            Updated quota status
        """
        quota = self.get_or_create_quota(user_id)

        # Update the record
        quota_model = self.model().where({"id": quota["id"]}).first()
        if quota_model:
            if is_gps_enhanced:
                quota_model.items["gps_enhanced_requests"] += 1
                logger.info(
                    f"Incremented GPS-enhanced requests for user {user_id}: {quota_model.items['gps_enhanced_requests']}/{quota_model.items['quota_limit']}"
                )
            else:
                quota_model.items["pincode_requests"] += 1
                logger.info(
                    f"Incremented pincode requests for user {user_id}: {quota_model.items['pincode_requests']}"
                )

            # Save using update
            self.model().and_where_custom([["id", "=", quota["id"]]]).update(quota_model.items)

        return await self.get_quota_status(user_id)

    async def get_quota_status(self, user_id: Union[int, str]) -> QuotaStatusResponse:
        """
        Get current quota status for user

        Args:
            user_id: User ID (integer from users.id)

        Returns:
            QuotaStatusResponse with current usage
        """
        quota = self.get_or_create_quota(user_id)

        remaining = max(0, quota["quota_limit"] - quota["gps_enhanced_requests"])
        exceeded = quota["gps_enhanced_requests"] >= quota["quota_limit"]

        # Calculate next reset time (midnight IST)
        now_ist = datetime.now(self.IST_TIMEZONE)
        next_reset = (now_ist + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return QuotaStatusResponse(
            user_id=str(user_id),
            date=quota["date"],
            gps_enhanced_requests=quota["gps_enhanced_requests"],
            pincode_requests=quota["pincode_requests"],
            quota_limit=quota["quota_limit"],
            remaining_quota=remaining,
            quota_exceeded=exceeded,
            next_reset=next_reset,
        )

    async def reset_daily_quota(self) -> QuotaResetResponse:
        """
        Reset quota for all users (called by scheduled job at midnight IST)

        Returns:
            QuotaResetResponse with reset statistics
        """
        today = datetime.now(self.IST_TIMEZONE).date()
        reset_time = datetime.now(self.IST_TIMEZONE)

        # Get all quota records for today
        quotas_model = self.model().and_where_custom([["date", "=", str(today)]]).get()

        users_reset = 0
        if quotas_model and quotas_model.items:
            for quota in quotas_model.items:
                self.model().and_where_custom([["id", "=", quota["id"]]]).update(
                    {"gps_enhanced_requests": 0, "pincode_requests": 0, "last_reset": reset_time}
                )
                users_reset += 1

        logger.info(f"Reset quota for {users_reset} users at {reset_time}")

        return QuotaResetResponse(
            users_reset=users_reset,
            reset_time=reset_time,
            message=f"Successfully reset quota for {users_reset} users",
        )

    async def update_quota_limit(
        self, user_id: Union[int, str], new_limit: int
    ) -> QuotaStatusResponse:
        """
        Update quota limit for specific user (admin function)

        Args:
            user_id: User ID (integer from users.id)
            new_limit: New quota limit

        Returns:
            Updated quota status
        """
        quota = self.get_or_create_quota(user_id)

        self.model().and_where_custom([["id", "=", quota["id"]]]).update({"quota_limit": new_limit})

        logger.info(f"Updated quota limit for user {user_id} to {new_limit}")

        return await self.get_quota_status(user_id)

    async def get_usage_statistics(self, start_date: date, end_date: date) -> dict:
        """
        Get usage statistics for date range (admin function)

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with usage statistics
        """
        # Get all quota records in date range using custom where
        quotas = (
            self.model()
            .and_where_custom([["date", ">=", str(start_date)], ["date", "<=", str(end_date)]])
            .get()
        )

        if not quotas or not quotas.items:
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_users": 0,
                "total_gps_requests": 0,
                "total_pincode_requests": 0,
                "avg_gps_requests_per_user": 0.0,
                "avg_pincode_requests_per_user": 0.0,
            }

        total_gps = 0
        total_pincode = 0
        total_users = 0

        for quota in quotas.items:
            total_gps += quota.get("gps_enhanced_requests", 0)
            total_pincode += quota.get("pincode_requests", 0)
            total_users += 1

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_users": total_users,
            "total_gps_requests": total_gps,
            "total_pincode_requests": total_pincode,
            "avg_gps_requests_per_user": float(total_gps / total_users) if total_users > 0 else 0.0,
            "avg_pincode_requests_per_user": (
                float(total_pincode / total_users) if total_users > 0 else 0.0
            ),
        }
