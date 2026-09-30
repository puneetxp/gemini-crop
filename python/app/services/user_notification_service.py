from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.user_notification import UserNotification


class UserNotificationService(CrudService):
    model = UserNotification


# Singleton instance
_service = UserNotificationService()


# Generic getter (for auto-generated routers)
def get_service() -> UserNotificationService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_user_notification_service() -> UserNotificationService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
