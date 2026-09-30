"""
Notification management API endpoints
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import DB, CurrentAdmin, CurrentUser
from app.services import notification_inbox
from app.services.notification_service import notification_service
from app.services.web_push_service import web_push_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionRequest(BaseModel):
    """Browser PushSubscription as sent by notification.service.ts"""

    endpoint: str
    keys: PushKeys


class SendNotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
    url: str = "/"
    type: str = "general"
    data: Optional[Dict[str, Any]] = None


@router.get("/vapid-public-key", response_model=Dict[str, Any])
async def get_vapid_public_key():
    """Public VAPID key the browser needs to subscribe"""
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Web push is not configured")
    return {"success": True, "public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=Dict[str, Any])
async def subscribe_notifications(
    subscription: PushSubscriptionRequest,
    request: Request,
    current_user: CurrentUser,
):
    """Save the current browser's push subscription for the current user"""
    try:
        record = web_push_service.subscribe(
            user_id=current_user.id,
            endpoint=subscription.endpoint,
            p256dh=subscription.keys.p256dh,
            auth=subscription.keys.auth,
            user_agent=request.headers.get("user-agent"),
        )
        return {
            "success": True,
            "message": "Subscribed to notifications successfully",
            "subscription_id": record.get("id"),
        }
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe", response_model=Dict[str, Any])
async def unsubscribe_notifications(
    subscription: PushSubscriptionRequest,
    current_user: CurrentUser,
):
    """Remove the current browser's push subscription"""
    try:
        web_push_service.unsubscribe(current_user.id, subscription.endpoint)
        return {"success": True, "message": "Unsubscribed from notifications successfully"}
    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", response_model=Dict[str, Any])
async def send_notification(
    notification: SendNotificationRequest,
    current_user: CurrentAdmin,
):
    """Send a web push notification to a user (Admin only)"""
    try:
        result = web_push_service.send_to_user(
            user_id=notification.user_id,
            title=notification.title,
            body=notification.body,
            url=notification.url,
            notification_type=notification.type,
            extra=notification.data,
        )
        return {
            "success": result["sent"] > 0,
            "message": (
                "Notification sent successfully"
                if result["sent"]
                else "User has no active push subscriptions"
            ),
            **result,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=Dict[str, Any])
async def send_test_notification(current_user: CurrentUser):
    """Send a test push to all of the current user's subscribed browsers"""
    try:
        result = web_push_service.send_to_user(
            user_id=current_user.id,
            title="Test Notification",
            body="Push notifications from CropSense AI are working.",
            url="/",
        )
        return {"success": result["sent"] > 0, **result}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── In-app inbox (user_notifications) ────────────────────────────────────────


@router.get("/inbox", response_model=Dict[str, Any])
async def get_inbox(
    current_user: CurrentUser,
    unread_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """The signed-in user's notifications, newest first, with the unread count"""
    return notification_inbox.list_for(current_user.id, unread_only, skip, limit)


@router.post("/read-all", response_model=Dict[str, Any])
async def mark_all_notifications_read(current_user: CurrentUser):
    """Mark every unread notification of the signed-in user as read"""
    return {"success": True, "updated": notification_inbox.mark_all_read(current_user.id)}


@router.post("/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_read(notification_id: int, current_user: CurrentUser):
    """Mark one of the signed-in user's notifications as read"""
    try:
        return notification_inbox.mark_read(notification_id, current_user.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
