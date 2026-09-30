"""
Web Push Service
Stores browser push subscriptions and delivers notifications to them via VAPID.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pywebpush import WebPushException, webpush

from app.core.config import settings
from app.orm.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


class WebPushService:
    """Service for managing browser push subscriptions and sending web push"""

    def __init__(self):
        self.model = PushSubscription

    @property
    def configured(self) -> bool:
        return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)

    def subscribe(
        self,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a browser subscription for a user (replaces any existing row for the endpoint)"""
        # An endpoint belongs to one browser; re-subscribing (or a different user
        # logging in on the same browser) takes it over.
        self.model.delete({"endpoint": endpoint})
        result = self.model.create(
            {
                "user_id": user_id,
                "endpoint": endpoint,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": (user_agent or "")[:512] or None,
            }
        ).get_inserted()
        logger.info(f"Saved push subscription {result['id']} for user {user_id}")
        return result.to_dict()

    def unsubscribe(self, user_id: int, endpoint: str) -> bool:
        """Remove a user's subscription for an endpoint"""
        return self.model.delete({"user_id": user_id, "endpoint": endpoint}) > 0

    def _subscriptions_for(self, user_id: int) -> List[Dict[str, Any]]:
        results = self.model.where({"user_id": user_id, "enable": 1}).get()
        records = results.to_dict() if results else []
        if isinstance(records, dict):
            records = [records]
        return records

    def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        url: str = "/",
        notification_type: str = "general",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Push a notification to every browser the user has subscribed"""
        # Keep a copy in the in-app inbox, even if push isn't configured or the user has no subscription
        from app.services import notification_inbox

        notification_inbox.add(user_id, title, body, notification_type, url, extra)
        if not self.configured:
            raise RuntimeError(
                "Web push is not configured (VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY missing)"
            )

        payload = json.dumps(
            {
                "title": title,
                "body": body,
                "url": url,
                "type": notification_type,
                **(extra or {}),
            }
        )

        sent, removed, failed = 0, 0, 0
        for sub in self._subscriptions_for(user_id):
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                    },
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": settings.VAPID_SUBJECT},
                    ttl=86400,
                )
                sent += 1
            except WebPushException as e:
                status_code = e.response.status_code if e.response is not None else None
                if status_code in (404, 410):
                    # Browser dropped the subscription; clean it up.
                    self.model.delete({"id": sub["id"]})
                    removed += 1
                else:
                    logger.error(f"Web push to subscription {sub['id']} failed: {e}")
                    failed += 1

        logger.info(f"Web push to user {user_id}: sent={sent} removed={removed} failed={failed}")
        return {"sent": sent, "removed": removed, "failed": failed}


# Singleton instance
web_push_service = WebPushService()
