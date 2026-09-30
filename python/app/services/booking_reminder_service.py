"""
Booking Reminder Service for scheduled notifications
Handles payment reminders, overdue alerts, and quality verification reminders
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from app.orm.advance_booking import AdvanceBooking
from app.orm.marketplace_listing import MarketplaceListing
from app.orm.payment_milestone import PaymentMilestone
from app.orm.user import User
from app.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


class BookingReminderService:
    """
    Service for managing booking-related reminders and scheduled notifications

    Validates: Requirements AC16 (Phase 11 - Booking notifications and reminders)
    """

    def __init__(self):
        """Initialize booking reminder service"""
        self.notification_service = get_notification_service()

    def send_payment_reminders(self, days_before_due: int = 7) -> Dict[str, Any]:
        """
        Send payment reminders for milestones due in specified days

        Args:
            days_before_due: Number of days before due date to send reminder (default: 7)

        Returns:
            Dictionary with reminder statistics

        Validates: Requirements AC16 (Phase 11 - Payment reminders 7 days before due)
        """
        try:
            # Calculate target date
            target_date = date.today() + timedelta(days=days_before_due)

            # Find pending payment milestones due on target date
            milestones = PaymentMilestone().where("status", "pending").get()

            reminders_sent = 0
            reminders_failed = 0

            for milestone in milestones:
                # Check if due date matches target
                milestone_due_date = milestone.due_date
                if isinstance(milestone_due_date, datetime):
                    milestone_due_date = milestone_due_date.date()

                if milestone_due_date != target_date:
                    continue

                # Get booking details
                booking = AdvanceBooking().where("id", milestone.booking_id).first()
                if not booking:
                    logger.warning(f"Booking not found for milestone {milestone.id}")
                    continue

                # Get buyer details (payment is buyer's responsibility)
                buyer = User().where("id", booking.buyer_id).first()
                if not buyer or not buyer.phone:
                    logger.warning(f"Buyer not found or no phone for booking {booking.id}")
                    continue

                # Get listing for crop type
                listing = MarketplaceListing().where("id", booking.listing_id).first()
                crop_type = listing.crop_type if listing else "Crop"

                # Send reminder
                result = self.notification_service.send_payment_reminder_notification(
                    recipient_phone=buyer.phone,
                    recipient_email=buyer.email,
                    recipient_name=buyer.name or "Buyer",
                    booking_id=booking.id,
                    milestone_type=milestone.milestone_type,
                    amount=float(milestone.amount),
                    due_date=(
                        milestone.due_date
                        if isinstance(milestone.due_date, datetime)
                        else datetime.combine(milestone.due_date, datetime.min.time())
                    ),
                    crop_type=crop_type,
                    days_until_due=days_before_due,
                )

                if result.get("success"):
                    reminders_sent += 1
                else:
                    reminders_failed += 1

            logger.info(f"Payment reminders: {reminders_sent} sent, {reminders_failed} failed")

            return {
                "success": True,
                "reminders_sent": reminders_sent,
                "reminders_failed": reminders_failed,
                "target_date": target_date.isoformat(),
                "days_before_due": days_before_due,
            }

        except Exception as e:
            logger.error(f"Error sending payment reminders: {e}")
            return {"success": False, "error": str(e), "reminders_sent": 0, "reminders_failed": 0}

    def send_overdue_payment_alerts(self) -> Dict[str, Any]:
        """
        Send alerts for overdue payments

        Returns:
            Dictionary with alert statistics

        Validates: Requirements AC16 (Phase 11 - Overdue payment alerts)
        """
        try:
            today = date.today()

            # Find overdue payment milestones
            milestones = PaymentMilestone().where("status", "pending").get()

            alerts_sent = 0
            alerts_failed = 0

            for milestone in milestones:
                # Check if overdue
                milestone_due_date = milestone.due_date
                if isinstance(milestone_due_date, datetime):
                    milestone_due_date = milestone_due_date.date()

                if milestone_due_date >= today:
                    continue  # Not overdue yet

                days_overdue = (today - milestone_due_date).days

                # Get booking details
                booking = AdvanceBooking().where("id", milestone.booking_id).first()
                if not booking:
                    logger.warning(f"Booking not found for milestone {milestone.id}")
                    continue

                # Get buyer details
                buyer = User().where("id", booking.buyer_id).first()
                if not buyer or not buyer.phone:
                    logger.warning(f"Buyer not found or no phone for booking {booking.id}")
                    continue

                # Get listing for crop type
                listing = MarketplaceListing().where("id", booking.listing_id).first()
                crop_type = listing.crop_type if listing else "Crop"

                # Send overdue alert
                result = self.notification_service.send_payment_overdue_notification(
                    recipient_phone=buyer.phone,
                    recipient_email=buyer.email,
                    recipient_name=buyer.name or "Buyer",
                    booking_id=booking.id,
                    milestone_type=milestone.milestone_type,
                    amount=float(milestone.amount),
                    due_date=(
                        milestone.due_date
                        if isinstance(milestone.due_date, datetime)
                        else datetime.combine(milestone.due_date, datetime.min.time())
                    ),
                    crop_type=crop_type,
                    days_overdue=days_overdue,
                )

                if result.get("success"):
                    alerts_sent += 1
                else:
                    alerts_failed += 1

            logger.info(f"Overdue payment alerts: {alerts_sent} sent, {alerts_failed} failed")

            return {
                "success": True,
                "alerts_sent": alerts_sent,
                "alerts_failed": alerts_failed,
                "check_date": today.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending overdue payment alerts: {e}")
            return {"success": False, "error": str(e), "alerts_sent": 0, "alerts_failed": 0}

    def send_quality_verification_reminders(self, days_before_delivery: int = 3) -> Dict[str, Any]:
        """
        Send quality verification reminders before delivery date

        Args:
            days_before_delivery: Number of days before delivery to send reminder (default: 3)

        Returns:
            Dictionary with reminder statistics

        Validates: Requirements AC16 (Phase 11 - Quality verification reminders)
        """
        try:
            # Calculate target date
            target_date = date.today() + timedelta(days=days_before_delivery)

            # Find bookings with delivery date matching target
            bookings = AdvanceBooking().where("status", "confirmed").get()

            reminders_sent = 0
            reminders_failed = 0

            for booking in bookings:
                # Check if delivery date matches target
                delivery_date = booking.expected_delivery_date
                if isinstance(delivery_date, datetime):
                    delivery_date = delivery_date.date()

                if delivery_date != target_date:
                    continue

                # Get farmer details (quality verification is farmer's responsibility)
                farmer = User().where("id", booking.farmer_id).first()
                if not farmer or not farmer.phone:
                    logger.warning(f"Farmer not found or no phone for booking {booking.id}")
                    continue

                # Get listing for crop type
                listing = MarketplaceListing().where("id", booking.listing_id).first()
                crop_type = listing.crop_type if listing else "Crop"

                # Send reminder
                result = self.notification_service.send_quality_verification_reminder(
                    recipient_phone=farmer.phone,
                    recipient_email=farmer.email,
                    recipient_name=farmer.name or "Farmer",
                    booking_id=booking.id,
                    crop_type=crop_type,
                    expected_delivery_date=(
                        booking.expected_delivery_date
                        if isinstance(booking.expected_delivery_date, datetime)
                        else datetime.combine(booking.expected_delivery_date, datetime.min.time())
                    ),
                    days_until_delivery=days_before_delivery,
                )

                if result.get("success"):
                    reminders_sent += 1
                else:
                    reminders_failed += 1

            logger.info(
                f"Quality verification reminders: {reminders_sent} sent, {reminders_failed} failed"
            )

            return {
                "success": True,
                "reminders_sent": reminders_sent,
                "reminders_failed": reminders_failed,
                "target_date": target_date.isoformat(),
                "days_before_delivery": days_before_delivery,
            }

        except Exception as e:
            logger.error(f"Error sending quality verification reminders: {e}")
            return {"success": False, "error": str(e), "reminders_sent": 0, "reminders_failed": 0}

    def run_all_scheduled_reminders(self) -> Dict[str, Any]:
        """
        Run all scheduled reminder tasks

        Returns:
            Dictionary with combined statistics

        Validates: Requirements AC16 (Phase 11 - All booking reminders)
        """
        try:
            # Send payment reminders (7 days before due)
            payment_reminders = self.send_payment_reminders(days_before_due=7)

            # Send overdue payment alerts
            overdue_alerts = self.send_overdue_payment_alerts()

            # Send quality verification reminders (3 days before delivery)
            quality_reminders = self.send_quality_verification_reminders(days_before_delivery=3)

            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "payment_reminders": payment_reminders,
                "overdue_alerts": overdue_alerts,
                "quality_reminders": quality_reminders,
                "total_notifications_sent": (
                    payment_reminders.get("reminders_sent", 0)
                    + overdue_alerts.get("alerts_sent", 0)
                    + quality_reminders.get("reminders_sent", 0)
                ),
            }

        except Exception as e:
            logger.error(f"Error running scheduled reminders: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}


# Create singleton instance
booking_reminder_service = BookingReminderService()


def get_booking_reminder_service() -> BookingReminderService:
    """Get booking reminder service instance"""
    return booking_reminder_service
