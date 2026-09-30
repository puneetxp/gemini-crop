"""
Notification Service for managing notifications via Amazon SNS
Handles buyer interest notifications, strategy reminders, weather alerts, and harvest reminders
"""

# AWS imports removed for GCP/local migration
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications via Amazon SNS

    Validates: Requirements AC4, AC6
    """

    def __init__(self):
        """Initialize GCloud/Local Notification client"""
        self.sns_enabled = False
        self.sns_client = None
        logger.info("Local/GCloud notification service initialized (AWS SNS removed)")

        # Topic ARNs (retained with fallbacks for compatibility after AWS removal)
        self.topic_buyer_interest = getattr(settings, "SNS_TOPIC_ARN_BUYER_INTEREST", None)
        self.topic_strategy_reminders = getattr(settings, "SNS_TOPIC_ARN_STRATEGY_REMINDERS", None)
        self.topic_weather_alerts = getattr(settings, "SNS_TOPIC_ARN_WEATHER_ALERTS", None)
        self.topic_harvest_reminders = getattr(settings, "SNS_TOPIC_ARN_HARVEST_REMINDERS", None)
        self.topic_booking_notifications = getattr(
            settings, "SNS_TOPIC_ARN_BOOKING_NOTIFICATIONS", None
        )

        # Notification tracking
        self.notification_history: List[Dict[str, Any]] = []
        self.retry_queue: List[Dict[str, Any]] = []

    def send_buyer_interest_notification(
        self,
        farmer_phone: str,
        farmer_email: Optional[str],
        buyer_name: str,
        crop_type: str,
        quantity_interested: float,
        listing_id: str,
        buyer_contact: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to farmer when buyer expresses interest

        Args:
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email address (optional)
            buyer_name: Name of the buyer
            crop_type: Type of crop
            quantity_interested: Quantity buyer is interested in
            listing_id: Marketplace listing ID
            buyer_contact: Buyer's contact information (optional)

        Returns:
            Dictionary with notification status and details

        Validates: AC4 - Notify farmer when buyer expresses interest
        """
        try:
            # Create notification message
            subject = f"New Buyer Interest: {crop_type}"
            message = self._format_buyer_interest_message(
                buyer_name=buyer_name,
                crop_type=crop_type,
                quantity_interested=quantity_interested,
                buyer_contact=buyer_contact,
            )

            # Send notification
            result = self._send_notification(
                topic_arn=self.topic_buyer_interest,
                subject=subject,
                message=message,
                phone_number=farmer_phone,
                email=farmer_email,
                notification_type="buyer_interest",
                metadata={
                    "listing_id": listing_id,
                    "buyer_name": buyer_name,
                    "crop_type": crop_type,
                    "quantity": quantity_interested,
                },
            )

            logger.info(f"Buyer interest notification sent for listing {listing_id}")
            return result

        except Exception as e:
            logger.error(f"Error sending buyer interest notification: {e}")
            return {"success": False, "error": str(e), "notification_type": "buyer_interest"}

    def send_strategy_reminder(
        self,
        farmer_phone: str,
        farmer_email: Optional[str],
        farmer_name: str,
        strategy_id: str,
        reminder_type: str,
        action_items: List[str],
        due_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Send monthly strategy implementation reminder to farmer

        Args:
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email address (optional)
            farmer_name: Farmer's name
            strategy_id: Annual strategy ID
            reminder_type: Type of reminder (planting, fertilizer, harvest, etc.)
            action_items: List of action items for this month
            due_date: Due date for actions (optional)

        Returns:
            Dictionary with notification status and details

        Validates: AC6 - Monthly reminders based on timeline
        """
        try:
            # Create notification message
            subject = f"Farm Strategy Reminder: {reminder_type.title()}"
            message = self._format_strategy_reminder_message(
                farmer_name=farmer_name,
                reminder_type=reminder_type,
                action_items=action_items,
                due_date=due_date,
            )

            # Send notification
            result = self._send_notification(
                topic_arn=self.topic_strategy_reminders,
                subject=subject,
                message=message,
                phone_number=farmer_phone,
                email=farmer_email,
                notification_type="strategy_reminder",
                metadata={
                    "strategy_id": strategy_id,
                    "reminder_type": reminder_type,
                    "action_count": len(action_items),
                },
            )

            logger.info(f"Strategy reminder sent for strategy {strategy_id}")
            return result

        except Exception as e:
            logger.error(f"Error sending strategy reminder: {e}")
            return {"success": False, "error": str(e), "notification_type": "strategy_reminder"}

    def send_weather_alert(
        self,
        farmer_phone: str,
        farmer_email: Optional[str],
        alert_type: str,
        severity: str,
        message: str,
        recommendation: Optional[str] = None,
        valid_until: Optional[datetime] = None,
        affected_crops: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send weather alert notification for extreme conditions

        Args:
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email address (optional)
            alert_type: Type of alert (storm, hail, extreme_heat, etc.)
            severity: Severity level (low, medium, high, critical)
            message: Alert message
            recommendation: Recommended actions (optional)
            valid_until: Alert validity period (optional)
            affected_crops: List of affected crops (optional)

        Returns:
            Dictionary with notification status and details

        Validates: AC6 - Basic weather alert notifications for extreme conditions
        """
        try:
            # Create notification message
            subject = (
                f"⚠️ Weather Alert: {alert_type.replace('_', ' ').title()} ({severity.upper()})"
            )
            formatted_message = self._format_weather_alert_message(
                alert_type=alert_type,
                severity=severity,
                message=message,
                recommendation=recommendation,
                valid_until=valid_until,
                affected_crops=affected_crops,
            )

            # Send notification
            result = self._send_notification(
                topic_arn=self.topic_weather_alerts,
                subject=subject,
                message=formatted_message,
                phone_number=farmer_phone,
                email=farmer_email,
                notification_type="weather_alert",
                metadata={
                    "alert_type": alert_type,
                    "severity": severity,
                    "affected_crops": affected_crops or [],
                },
            )

            logger.info(f"Weather alert sent: {alert_type} ({severity})")
            return result

        except Exception as e:
            logger.error(f"Error sending weather alert: {e}")
            return {"success": False, "error": str(e), "notification_type": "weather_alert"}

    def send_harvest_reminder(
        self,
        farmer_phone: str,
        farmer_email: Optional[str],
        farmer_name: str,
        crop_type: str,
        expected_harvest_date: datetime,
        estimated_yield: float,
        preparation_tasks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send harvest timing reminder (1 week before expected harvest)

        Args:
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email address (optional)
            farmer_name: Farmer's name
            crop_type: Type of crop
            expected_harvest_date: Expected harvest date
            estimated_yield: Estimated yield in quintals
            preparation_tasks: List of preparation tasks (optional)

        Returns:
            Dictionary with notification status and details

        Validates: AC6 - Notify farmer 1 week before expected harvest
        """
        try:
            # Create notification message
            subject = f"Harvest Reminder: {crop_type} Ready Soon"
            message = self._format_harvest_reminder_message(
                farmer_name=farmer_name,
                crop_type=crop_type,
                expected_harvest_date=expected_harvest_date,
                estimated_yield=estimated_yield,
                preparation_tasks=preparation_tasks,
            )

            # Send notification
            result = self._send_notification(
                topic_arn=self.topic_harvest_reminders,
                subject=subject,
                message=message,
                phone_number=farmer_phone,
                email=farmer_email,
                notification_type="harvest_reminder",
                metadata={
                    "crop_type": crop_type,
                    "harvest_date": expected_harvest_date.isoformat(),
                    "estimated_yield": estimated_yield,
                },
            )

            logger.info(f"Harvest reminder sent for {crop_type}")
            return result

        except Exception as e:
            logger.error(f"Error sending harvest reminder: {e}")
            return {"success": False, "error": str(e), "notification_type": "harvest_reminder"}

    def send_booking_created_notification(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        recipient_name: str,
        recipient_role: str,  # 'buyer' or 'farmer'
        booking_id: int,
        crop_type: str,
        quantity: float,
        total_amount: float,
        expected_delivery_date: datetime,
        other_party_name: str,
    ) -> Dict[str, Any]:
        """
        Send notification when booking is created

        Args:
            recipient_phone: Recipient's phone number
            recipient_email: Recipient's email address (optional)
            recipient_name: Recipient's name
            recipient_role: 'buyer' or 'farmer'
            booking_id: Booking ID
            crop_type: Type of crop
            quantity: Quantity booked
            total_amount: Total booking amount
            expected_delivery_date: Expected delivery date
            other_party_name: Name of the other party (buyer/farmer)

        Returns:
            Dictionary with notification status and details

        Validates: Requirements AC16 (Phase 11 - Booking notifications)
        """
        try:
            subject = f"New Booking Created: {crop_type}"
            message = self._format_booking_created_message(
                recipient_name=recipient_name,
                recipient_role=recipient_role,
                booking_id=booking_id,
                crop_type=crop_type,
                quantity=quantity,
                total_amount=total_amount,
                expected_delivery_date=expected_delivery_date,
                other_party_name=other_party_name,
            )

            result = self._send_notification(
                topic_arn=self.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=recipient_phone,
                email=recipient_email,
                notification_type="booking_created",
                metadata={
                    "booking_id": booking_id,
                    "recipient_role": recipient_role,
                    "crop_type": crop_type,
                    "quantity": quantity,
                    "total_amount": total_amount,
                },
            )

            logger.info(
                f"Booking created notification sent for booking {booking_id} to {recipient_role}"
            )
            return result

        except Exception as e:
            logger.error(f"Error sending booking created notification: {e}")
            return {"success": False, "error": str(e), "notification_type": "booking_created"}

    def send_payment_reminder_notification(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        recipient_name: str,
        booking_id: int,
        milestone_type: str,
        amount: float,
        due_date: datetime,
        crop_type: str,
        days_until_due: int,
    ) -> Dict[str, Any]:
        """
        Send payment reminder notification (7 days before due date)

        Args:
            recipient_phone: Recipient's phone number
            recipient_email: Recipient's email address (optional)
            recipient_name: Recipient's name
            booking_id: Booking ID
            milestone_type: Payment milestone type
            amount: Payment amount
            due_date: Payment due date
            crop_type: Type of crop
            days_until_due: Days until payment is due

        Returns:
            Dictionary with notification status and details

        Validates: Requirements AC16 (Phase 11 - Payment reminders)
        """
        try:
            subject = f"Payment Reminder: {milestone_type.replace('_', ' ').title()} Due Soon"
            message = self._format_payment_reminder_message(
                recipient_name=recipient_name,
                booking_id=booking_id,
                milestone_type=milestone_type,
                amount=amount,
                due_date=due_date,
                crop_type=crop_type,
                days_until_due=days_until_due,
            )

            result = self._send_notification(
                topic_arn=self.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=recipient_phone,
                email=recipient_email,
                notification_type="payment_reminder",
                metadata={
                    "booking_id": booking_id,
                    "milestone_type": milestone_type,
                    "amount": amount,
                    "due_date": due_date.isoformat(),
                    "days_until_due": days_until_due,
                },
            )

            logger.info(
                f"Payment reminder sent for booking {booking_id}, milestone {milestone_type}"
            )
            return result

        except Exception as e:
            logger.error(f"Error sending payment reminder: {e}")
            return {"success": False, "error": str(e), "notification_type": "payment_reminder"}

    def send_payment_overdue_notification(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        recipient_name: str,
        booking_id: int,
        milestone_type: str,
        amount: float,
        due_date: datetime,
        crop_type: str,
        days_overdue: int,
    ) -> Dict[str, Any]:
        """
        Send overdue payment alert notification

        Args:
            recipient_phone: Recipient's phone number
            recipient_email: Recipient's email address (optional)
            recipient_name: Recipient's name
            booking_id: Booking ID
            milestone_type: Payment milestone type
            amount: Payment amount
            due_date: Payment due date
            crop_type: Type of crop
            days_overdue: Days payment is overdue

        Returns:
            Dictionary with notification status and details

        Validates: Requirements AC16 (Phase 11 - Overdue payment alerts)
        """
        try:
            subject = f"⚠️ Payment Overdue: {milestone_type.replace('_', ' ').title()}"
            message = self._format_payment_overdue_message(
                recipient_name=recipient_name,
                booking_id=booking_id,
                milestone_type=milestone_type,
                amount=amount,
                due_date=due_date,
                crop_type=crop_type,
                days_overdue=days_overdue,
            )

            result = self._send_notification(
                topic_arn=self.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=recipient_phone,
                email=recipient_email,
                notification_type="payment_overdue",
                metadata={
                    "booking_id": booking_id,
                    "milestone_type": milestone_type,
                    "amount": amount,
                    "due_date": due_date.isoformat(),
                    "days_overdue": days_overdue,
                },
            )

            logger.info(
                f"Payment overdue alert sent for booking {booking_id}, milestone {milestone_type}"
            )
            return result

        except Exception as e:
            logger.error(f"Error sending payment overdue notification: {e}")
            return {"success": False, "error": str(e), "notification_type": "payment_overdue"}

    def send_quality_verification_reminder(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        recipient_name: str,
        booking_id: int,
        crop_type: str,
        expected_delivery_date: datetime,
        days_until_delivery: int,
    ) -> Dict[str, Any]:
        """
        Send quality verification reminder notification

        Args:
            recipient_phone: Recipient's phone number
            recipient_email: Recipient's email address (optional)
            recipient_name: Recipient's name
            booking_id: Booking ID
            crop_type: Type of crop
            expected_delivery_date: Expected delivery date
            days_until_delivery: Days until delivery

        Returns:
            Dictionary with notification status and details

        Validates: Requirements AC16 (Phase 11 - Quality verification reminders)
        """
        try:
            subject = f"Quality Verification Reminder: {crop_type}"
            message = self._format_quality_verification_reminder_message(
                recipient_name=recipient_name,
                booking_id=booking_id,
                crop_type=crop_type,
                expected_delivery_date=expected_delivery_date,
                days_until_delivery=days_until_delivery,
            )

            result = self._send_notification(
                topic_arn=self.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=recipient_phone,
                email=recipient_email,
                notification_type="quality_verification_reminder",
                metadata={
                    "booking_id": booking_id,
                    "crop_type": crop_type,
                    "expected_delivery_date": expected_delivery_date.isoformat(),
                    "days_until_delivery": days_until_delivery,
                },
            )

            logger.info(f"Quality verification reminder sent for booking {booking_id}")
            return result

        except Exception as e:
            logger.error(f"Error sending quality verification reminder: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification_type": "quality_verification_reminder",
            }

    def send_booking_status_update_notification(
        self,
        recipient_phone: str,
        recipient_email: Optional[str],
        recipient_name: str,
        recipient_role: str,  # 'buyer' or 'farmer'
        booking_id: int,
        crop_type: str,
        old_status: str,
        new_status: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send booking status update notification

        Args:
            recipient_phone: Recipient's phone number
            recipient_email: Recipient's email address (optional)
            recipient_name: Recipient's name
            recipient_role: 'buyer' or 'farmer'
            booking_id: Booking ID
            crop_type: Type of crop
            old_status: Previous status
            new_status: New status
            notes: Additional notes (optional)

        Returns:
            Dictionary with notification status and details

        Validates: Requirements AC16 (Phase 11 - Booking status updates)
        """
        try:
            subject = f"Booking Status Update: {new_status.replace('_', ' ').title()}"
            message = self._format_booking_status_update_message(
                recipient_name=recipient_name,
                recipient_role=recipient_role,
                booking_id=booking_id,
                crop_type=crop_type,
                old_status=old_status,
                new_status=new_status,
                notes=notes,
            )

            result = self._send_notification(
                topic_arn=self.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=recipient_phone,
                email=recipient_email,
                notification_type="booking_status_update",
                metadata={
                    "booking_id": booking_id,
                    "recipient_role": recipient_role,
                    "crop_type": crop_type,
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )

            logger.info(
                f"Booking status update notification sent for booking {booking_id} to {recipient_role}"
            )
            return result

        except Exception as e:
            logger.error(f"Error sending booking status update notification: {e}")
            return {"success": False, "error": str(e), "notification_type": "booking_status_update"}

    def _send_notification(
        self,
        topic_arn: Optional[str],
        subject: str,
        message: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        notification_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Internal method to send notification via SNS with retry logic

        Args:
            topic_arn: SNS topic ARN
            subject: Notification subject
            message: Notification message
            phone_number: Phone number for SMS (optional)
            email: Email address (optional)
            notification_type: Type of notification
            metadata: Additional metadata (optional)

        Returns:
            Dictionary with notification status and details
        """
        notification_record = {
            "notification_type": notification_type,
            "subject": subject,
            "message": message,
            "phone_number": phone_number,
            "email": email,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "attempts": 0,
            "success": False,
            "message_id": None,
            "error": None,
        }

        # Also deliver to the recipient's subscribed browsers (never blocks SMS/email)
        notification_record["web_push"] = self._send_web_push(
            subject=subject,
            message=message,
            phone_number=phone_number,
            email=email,
            notification_type=notification_type,
            metadata=metadata,
        )

        # If SNS is disabled, log local notification and return success
        if not self.sns_enabled or not self.sns_client:
            logger.info(
                f"[NOTIFICATION MIGRATED TO LOCAL/GCLOUD] Type: {notification_type}, Subject: {subject}, Msg: {message[:100]}..."
            )
            notification_record["success"] = True
            notification_record["message_id"] = f"local-gcp-msg-{notification_type}"
            self.notification_history.append(notification_record)
            return notification_record

        # Check if topic ARN is configured
        if not topic_arn:
            logger.warning(f"Topic ARN not configured for {notification_type}")
            notification_record["success"] = False
            notification_record["error"] = "Topic ARN not configured"
            self.notification_history.append(notification_record)
            return notification_record

        # Try to send notification with retry logic
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(1, max_retries + 1):
            notification_record["attempts"] = attempt

            try:
                # Prepare message attributes
                message_attributes = {
                    "notification_type": {"DataType": "String", "StringValue": notification_type}
                }

                if phone_number:
                    message_attributes["phone_number"] = {
                        "DataType": "String",
                        "StringValue": phone_number,
                    }

                if email:
                    message_attributes["email"] = {"DataType": "String", "StringValue": email}

                # Publish to SNS topic
                response = self.sns_client.publish(
                    TopicArn=topic_arn,
                    Subject=subject,
                    Message=message,
                    MessageAttributes=message_attributes,
                )

                # Success
                notification_record["success"] = True
                notification_record["message_id"] = response.get("MessageId")
                logger.info(
                    f"Notification sent successfully: {notification_type} (MessageId: {response.get('MessageId')})"
                )
                break

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]
                logger.error(
                    f"SNS ClientError on attempt {attempt}/{max_retries}: {error_code} - {error_message}"
                )
                notification_record["error"] = f"{error_code}: {error_message}"

                # Retry on specific errors
                if error_code in ["Throttling", "ServiceUnavailable", "InternalError"]:
                    if attempt < max_retries:
                        import time

                        time.sleep(retry_delay * attempt)  # Exponential backoff
                        continue

                # Don't retry on other errors
                break

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}/{max_retries}: {e}")
                notification_record["error"] = str(e)

                if attempt < max_retries:
                    import time

                    time.sleep(retry_delay * attempt)
                    continue

                break

        # Add to history
        self.notification_history.append(notification_record)

        # Add to retry queue if failed
        if not notification_record["success"] and notification_record["attempts"] >= max_retries:
            self.retry_queue.append(notification_record)
            logger.warning(f"Notification added to retry queue: {notification_type}")

        return notification_record

    # Page each notification type opens when the user clicks it
    _WEB_PUSH_URLS = {
        "buyer_interest": "/marketplace/my-listings",
        "strategy_reminder": "/crops/annual-strategy/",
        "weather_alert": "/climate/hub",
        "harvest_reminder": "/crops/my-crops",
        "booking_created": "/marketplace/bookings",
        "booking_status_update": "/marketplace/bookings",
        "payment_reminder": "/marketplace/bookings",
        "payment_overdue": "/marketplace/bookings",
        "quality_verification_reminder": "/marketplace/bookings",
        "livestock_transaction": "/livestock/hub",
    }

    def _push_to_user(
        self,
        user_id: int,
        subject: str,
        message: str,
        notification_type: str,
    ) -> Dict[str, Any]:
        """Send a web push to one user; failures are logged, never raised"""
        try:
            from app.services.web_push_service import web_push_service

            if not web_push_service.configured:
                return {"skipped": "web push not configured"}

            # SMS/email bodies are long; keep the browser notification short
            body = " ".join(message.split())
            if len(body) > 180:
                body = body[:177] + "..."

            return web_push_service.send_to_user(
                user_id=user_id,
                title=subject,
                body=body,
                url=self._WEB_PUSH_URLS.get(notification_type, "/"),
                notification_type=notification_type,
            )
        except Exception as e:
            logger.error(f"Web push to user {user_id} failed: {e}")
            return {"error": str(e)}

    def _send_web_push(
        self,
        subject: str,
        message: str,
        phone_number: Optional[str],
        email: Optional[str],
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find the recipient by user_id, email or phone and push to their browsers"""
        try:
            metadata = metadata or {}
            user_id = metadata.get("user_id") or metadata.get("recipient_user_id")

            if not user_id and (email or phone_number):
                from app.orm.user import User

                user = User.find(email, "email") if email else None
                if not user and phone_number:
                    user = User.find(phone_number, "phone")
                user_id = user["id"] if user else None

            if not user_id:
                return None

            return self._push_to_user(int(user_id), subject, message, notification_type)
        except Exception as e:
            logger.error(f"Web push lookup failed for {notification_type}: {e}")
            return {"error": str(e)}

    def _format_buyer_interest_message(
        self,
        buyer_name: str,
        crop_type: str,
        quantity_interested: float,
        buyer_contact: Optional[str] = None,
    ) -> str:
        """Format buyer interest notification message"""
        message = f"""New Buyer Interest Alert!

A buyer is interested in your {crop_type} listing.

Buyer Details:
- Name: {buyer_name}
- Interested Quantity: {quantity_interested:.2f} quintals"""

        if buyer_contact:
            message += f"\n- Contact: {buyer_contact}"

        message += """

Please contact the buyer to discuss pricing and delivery terms.

Login to your CropSense AI account to view full details and manage this inquiry."""

        return message

    def _format_strategy_reminder_message(
        self,
        farmer_name: str,
        reminder_type: str,
        action_items: List[str],
        due_date: Optional[datetime] = None,
    ) -> str:
        """Format strategy reminder message"""
        message = f"""Hello {farmer_name},

This is your monthly farming strategy reminder for {reminder_type.replace('_', ' ').title()}.

Action Items for This Month:"""

        for i, item in enumerate(action_items, 1):
            message += f"\n{i}. {item}"

        if due_date:
            message += f"\n\nDue Date: {due_date.strftime('%B %d, %Y')}"

        message += """

Login to CropSense AI to view your complete annual strategy and track your progress.

Good luck with your farming activities!"""

        return message

    def _format_weather_alert_message(
        self,
        alert_type: str,
        severity: str,
        message: str,
        recommendation: Optional[str] = None,
        valid_until: Optional[datetime] = None,
        affected_crops: Optional[List[str]] = None,
    ) -> str:
        """Format weather alert message"""
        formatted_message = f"""⚠️ WEATHER ALERT ⚠️

Alert Type: {alert_type.replace('_', ' ').title()}
Severity: {severity.upper()}

{message}"""

        if affected_crops:
            formatted_message += f"\n\nAffected Crops: {', '.join(affected_crops)}"

        if recommendation:
            formatted_message += f"\n\nRecommended Actions:\n{recommendation}"

        if valid_until:
            formatted_message += (
                f"\n\nAlert Valid Until: {valid_until.strftime('%B %d, %Y %I:%M %p')}"
            )

        formatted_message += "\n\nStay safe and protect your crops!"

        return formatted_message

    def _format_harvest_reminder_message(
        self,
        farmer_name: str,
        crop_type: str,
        expected_harvest_date: datetime,
        estimated_yield: float,
        preparation_tasks: Optional[List[str]] = None,
    ) -> str:
        """Format harvest reminder message"""
        message = f"""Hello {farmer_name},

Your {crop_type} crop is ready for harvest soon!

Harvest Details:
- Expected Date: {expected_harvest_date.strftime('%B %d, %Y')}
- Estimated Yield: {estimated_yield:.2f} quintals
- Days Until Harvest: {(expected_harvest_date - datetime.now()).days} days"""

        if preparation_tasks:
            message += "\n\nPreparation Tasks:"
            for i, task in enumerate(preparation_tasks, 1):
                message += f"\n{i}. {task}"

        message += """

Make sure you have:
✓ Arranged labor for harvesting
✓ Prepared storage facilities
✓ Contacted buyers if needed
✓ Checked weather forecast

Login to CropSense AI for detailed harvest guidance and market prices."""

        return message

    def _format_booking_created_message(
        self,
        recipient_name: str,
        recipient_role: str,
        booking_id: int,
        crop_type: str,
        quantity: float,
        total_amount: float,
        expected_delivery_date: datetime,
        other_party_name: str,
    ) -> str:
        """Format booking created notification message"""
        if recipient_role == "buyer":
            message = f"""Hello {recipient_name},

Your pre-harvest booking has been created successfully!

Booking Details:
- Booking ID: #{booking_id}
- Crop: {crop_type}
- Quantity: {quantity:.2f} quintals
- Total Amount: ₹{total_amount:,.2f}
- Expected Delivery: {expected_delivery_date.strftime('%B %d, %Y')}
- Farmer: {other_party_name}

Next Steps:
1. Complete advance payment to confirm booking
2. Track quality verification updates
3. Coordinate delivery logistics

Login to CropSense AI to view complete booking details and payment schedule."""
        else:  # farmer
            message = f"""Hello {recipient_name},

You have received a new pre-harvest booking!

Booking Details:
- Booking ID: #{booking_id}
- Crop: {crop_type}
- Quantity: {quantity:.2f} quintals
- Total Amount: ₹{total_amount:,.2f}
- Expected Delivery: {expected_delivery_date.strftime('%B %d, %Y')}
- Buyer: {other_party_name}

Next Steps:
1. Review booking terms and quality standards
2. Confirm booking acceptance
3. Prepare for quality verification

Login to CropSense AI to view complete booking details and contract terms."""

        return message

    def _format_payment_reminder_message(
        self,
        recipient_name: str,
        booking_id: int,
        milestone_type: str,
        amount: float,
        due_date: datetime,
        crop_type: str,
        days_until_due: int,
    ) -> str:
        """Format payment reminder message"""
        message = f"""Hello {recipient_name},

Payment Reminder for your {crop_type} booking.

Payment Details:
- Booking ID: #{booking_id}
- Milestone: {milestone_type.replace('_', ' ').title()}
- Amount Due: ₹{amount:,.2f}
- Due Date: {due_date.strftime('%B %d, %Y')}
- Days Until Due: {days_until_due} days

Please ensure timely payment to avoid delays in delivery.

Login to CropSense AI to make payment and view transaction details."""

        return message

    def _format_payment_overdue_message(
        self,
        recipient_name: str,
        booking_id: int,
        milestone_type: str,
        amount: float,
        due_date: datetime,
        crop_type: str,
        days_overdue: int,
    ) -> str:
        """Format payment overdue message"""
        message = f"""⚠️ PAYMENT OVERDUE ⚠️

Hello {recipient_name},

Your payment for {crop_type} booking is overdue.

Payment Details:
- Booking ID: #{booking_id}
- Milestone: {milestone_type.replace('_', ' ').title()}
- Amount Due: ₹{amount:,.2f}
- Due Date: {due_date.strftime('%B %d, %Y')}
- Days Overdue: {days_overdue} days

URGENT: Please make payment immediately to avoid:
- Late payment penalties
- Booking cancellation
- Impact on future bookings

Login to CropSense AI to make payment now."""

        return message

    def _format_quality_verification_reminder_message(
        self,
        recipient_name: str,
        booking_id: int,
        crop_type: str,
        expected_delivery_date: datetime,
        days_until_delivery: int,
    ) -> str:
        """Format quality verification reminder message"""
        message = f"""Hello {recipient_name},

Quality verification reminder for your {crop_type} booking.

Booking Details:
- Booking ID: #{booking_id}
- Crop: {crop_type}
- Expected Delivery: {expected_delivery_date.strftime('%B %d, %Y')}
- Days Until Delivery: {days_until_delivery} days

Action Required:
- Schedule quality verification inspection
- Prepare crop samples for testing
- Review quality standards in contract
- Ensure crop meets agreed specifications

Login to CropSense AI to schedule verification and view quality requirements."""

        return message

    def _format_booking_status_update_message(
        self,
        recipient_name: str,
        recipient_role: str,
        booking_id: int,
        crop_type: str,
        old_status: str,
        new_status: str,
        notes: Optional[str] = None,
    ) -> str:
        """Format booking status update message"""
        status_messages = {
            "confirmed": "Your booking has been confirmed!",
            "quality_check": "Quality verification is in progress.",
            "delivered": "Crop has been delivered successfully!",
            "cancelled": "Booking has been cancelled.",
        }

        message = f"""Hello {recipient_name},

Booking Status Update

Booking Details:
- Booking ID: #{booking_id}
- Crop: {crop_type}
- Previous Status: {old_status.replace('_', ' ').title()}
- New Status: {new_status.replace('_', ' ').title()}

{status_messages.get(new_status, 'Status has been updated.')}"""

        if notes:
            message += f"\n\nAdditional Notes:\n{notes}"

        if new_status == "confirmed":
            message += "\n\nNext Steps:\n- Track payment milestones\n- Prepare for quality verification\n- Monitor delivery schedule"
        elif new_status == "quality_check":
            message += "\n\nNext Steps:\n- Review quality verification results\n- Complete quality check payment\n- Coordinate final delivery"
        elif new_status == "delivered":
            message += "\n\nNext Steps:\n- Complete final payment\n- Provide feedback and rating\n- Thank you for using CropSense AI!"
        elif new_status == "cancelled":
            message += "\n\nIf you have questions about this cancellation, please contact support."

        message += "\n\nLogin to CropSense AI to view complete booking details."

        return message

    def get_notification_history(
        self, notification_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get notification history

        Args:
            notification_type: Filter by notification type (optional)
            limit: Maximum number of records to return

        Returns:
            List of notification records
        """
        history = self.notification_history

        if notification_type:
            history = [n for n in history if n["notification_type"] == notification_type]

        return history[-limit:]

    def get_retry_queue(self) -> List[Dict[str, Any]]:
        """
        Get notifications in retry queue

        Returns:
            List of failed notifications awaiting retry
        """
        return self.retry_queue.copy()

    def retry_failed_notifications(self) -> Dict[str, Any]:
        """
        Retry failed notifications from retry queue

        Returns:
            Dictionary with retry results
        """
        if not self.retry_queue:
            return {"total": 0, "retried": 0, "success": 0, "failed": 0}

        total = len(self.retry_queue)
        success_count = 0
        failed_count = 0

        # Process retry queue
        retry_queue_copy = self.retry_queue.copy()
        self.retry_queue.clear()

        for notification in retry_queue_copy:
            try:
                result = self._send_notification(
                    topic_arn=self._get_topic_arn_for_type(notification["notification_type"]),
                    subject=notification["subject"],
                    message=notification["message"],
                    phone_number=notification.get("phone_number"),
                    email=notification.get("email"),
                    notification_type=notification["notification_type"],
                    metadata=notification.get("metadata"),
                )

                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error retrying notification: {e}")
                failed_count += 1

        return {"total": total, "retried": total, "success": success_count, "failed": failed_count}

    def send_livestock_transaction_notification(
        self,
        transaction_id: int,
        seller_id: int,
        buyer_id: int,
        listing_id: int,
        notification_type: str,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification for livestock transaction events

        Args:
            transaction_id: Transaction ID
            seller_id: Seller user ID
            buyer_id: Buyer user ID
            listing_id: Listing ID
            notification_type: Type of notification (new_inquiry, seller_response, buyer_message,
                              status_update, completed, cancelled, bulk_inquiry)
            extra_data: Additional data for notification

        Returns:
            Dictionary with notification status and details
        """
        try:
            # Get user details (in real implementation, fetch from database)
            # For now, using placeholder logic

            subject = self._get_livestock_notification_subject(notification_type)
            message = self._format_livestock_transaction_message(
                transaction_id=transaction_id,
                notification_type=notification_type,
                extra_data=extra_data or {},
            )

            # Determine recipient based on notification type
            if notification_type in ["new_inquiry", "bulk_inquiry", "buyer_message"]:
                # Notify seller
                recipient_id = seller_id
            elif notification_type in ["seller_response", "completed"]:
                # Notify buyer
                recipient_id = buyer_id
            else:
                # Notify both (status_update, cancelled)
                recipient_id = None  # Will need to send to both

            # Push to the recipient's browsers (both parties when recipient_id is None)
            recipients = [recipient_id] if recipient_id else [seller_id, buyer_id]
            web_push = [
                self._push_to_user(uid, subject, message, "livestock_transaction")
                for uid in recipients
                if uid
            ]

            # Send notification (placeholder - would need actual phone/email from user record)
            result = {
                "web_push": web_push,
                "success": True,
                "notification_type": notification_type,
                "transaction_id": transaction_id,
                "recipient_id": recipient_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Track notification
            self.notification_history.append(
                {
                    "type": "livestock_transaction",
                    "notification_type": notification_type,
                    "transaction_id": transaction_id,
                    "result": result,
                    "timestamp": datetime.now(),
                }
            )

            logger.info(
                f"Livestock transaction notification sent: {notification_type} for transaction {transaction_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send livestock transaction notification: {e}")

            # Add to retry queue
            self.retry_queue.append(
                {
                    "type": "livestock_transaction",
                    "notification_type": notification_type,
                    "transaction_id": transaction_id,
                    "extra_data": extra_data,
                    "timestamp": datetime.now(),
                    "retry_count": 0,
                }
            )

            return {
                "success": False,
                "error": str(e),
                "notification_type": notification_type,
                "transaction_id": transaction_id,
            }

    def _get_livestock_notification_subject(self, notification_type: str) -> str:
        """Get subject line for livestock transaction notification"""
        subjects = {
            "new_inquiry": "New Livestock Inquiry",
            "bulk_inquiry": "New Bulk Livestock Inquiry",
            "seller_response": "Seller Response to Your Inquiry",
            "buyer_message": "New Message from Buyer",
            "status_update": "Transaction Status Updated",
            "completed": "Transaction Completed - Health Guarantee Active",
            "cancelled": "Transaction Cancelled",
        }
        return subjects.get(notification_type, "Livestock Transaction Update")

    def _format_livestock_transaction_message(
        self, transaction_id: int, notification_type: str, extra_data: Dict[str, Any]
    ) -> str:
        """Format livestock transaction notification message"""
        base_message = f"Transaction ID: {transaction_id}\n\n"

        if notification_type == "new_inquiry":
            return (
                base_message
                + "You have received a new inquiry for your livestock listing. Please review and respond promptly."
            )

        elif notification_type == "bulk_inquiry":
            total_qty = extra_data.get("total_quantity", 0)
            return (
                base_message
                + f"You have received a bulk inquiry for {total_qty} animals. Please review and respond promptly."
            )

        elif notification_type == "seller_response":
            return (
                base_message
                + "The seller has responded to your inquiry. Check the transaction details for their message."
            )

        elif notification_type == "buyer_message":
            return base_message + "The buyer has sent you a new message. Please review and respond."

        elif notification_type == "status_update":
            new_status = extra_data.get("new_status", "updated")
            return base_message + f"Transaction status has been updated to: {new_status}"

        elif notification_type == "completed":
            guarantee_expires = extra_data.get("health_guarantee_expires", "N/A")
            return (
                base_message
                + f"Transaction completed successfully! 7-day health guarantee is active until {guarantee_expires}."
            )

        elif notification_type == "cancelled":
            reason = extra_data.get("cancellation_reason", "No reason provided")
            return base_message + f"Transaction has been cancelled. Reason: {reason}"

        return base_message + "Transaction update available."

    def _get_topic_arn_for_type(self, notification_type: str) -> Optional[str]:
        """Get topic ARN for notification type"""
        topic_map = {
            "buyer_interest": self.topic_buyer_interest,
            "strategy_reminder": self.topic_strategy_reminders,
            "weather_alert": self.topic_weather_alerts,
            "harvest_reminder": self.topic_harvest_reminders,
            "booking_created": self.topic_booking_notifications,
            "payment_reminder": self.topic_booking_notifications,
            "payment_overdue": self.topic_booking_notifications,
            "quality_verification_reminder": self.topic_booking_notifications,
            "booking_status_update": self.topic_booking_notifications,
            "livestock_transaction": self.topic_booking_notifications,  # Reuse booking topic for now
        }
        return topic_map.get(notification_type)


# Create singleton instance
notification_service = NotificationService()


def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    return notification_service
