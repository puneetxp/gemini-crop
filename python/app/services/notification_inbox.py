"""
In-app notification inbox (table `user_notifications`).

Every push sent through web_push_service is also stored here, so the /notifications
page can show history even when the browser has no push subscription.
Kept out of the generated user_notification_service.py, which setup.php overwrites.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.core.db import DB

logger = logging.getLogger(__name__)


def add(
    user_id: int,
    title: str,
    message: str,
    type: str = "general",
    link: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Store a notification for a user. Never raises: a failed inbox write must not block the push."""
    try:
        rows = DB.raw(
            """INSERT INTO user_notifications (user_id, title, message, type, link, data, is_read)
               VALUES (?, ?, ?, ?, ?, ?, false) RETURNING *""",
            [user_id, title, message, type or "general", link, json.dumps(data) if data else None],
        ).result
        return rows[0] if rows else None
    except Exception as e:
        logger.warning(f"Could not store inbox notification for user {user_id}: {e}")
        return None


def list_for(
    user_id: int, unread_only: bool = False, skip: int = 0, limit: int = 50
) -> Dict[str, Any]:
    """The user's notifications, newest first, plus the unread count."""
    where = "user_id = ? AND enable = 1" + (" AND is_read = false" if unread_only else "")
    items = DB.raw(
        f"SELECT * FROM user_notifications WHERE {where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        [user_id, limit, skip],
    ).result
    unread = DB.raw(
        "SELECT COUNT(*) AS n FROM user_notifications WHERE user_id = ? AND enable = 1 AND is_read = false",
        [user_id],
    ).result
    return {"items": items, "unread_count": int(unread[0]["n"]) if unread else 0}


def mark_read(notification_id: int, user_id: int) -> Dict[str, Any]:
    """Mark one of the user's notifications as read. LookupError if it isn't theirs."""
    rows = DB.raw(
        """UPDATE user_notifications
           SET is_read = true, read_at = COALESCE(read_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP
           WHERE id = ? AND user_id = ? AND enable = 1 RETURNING *""",
        [notification_id, user_id],
    ).result
    if not rows:
        raise LookupError("Notification not found")
    return rows[0]


def mark_all_read(user_id: int) -> int:
    """Mark all of the user's unread notifications as read; returns how many changed."""
    rows = DB.raw(
        """UPDATE user_notifications
           SET is_read = true, read_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
           WHERE user_id = ? AND enable = 1 AND is_read = false RETURNING id""",
        [user_id],
    ).result
    return len(rows)
