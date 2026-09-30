from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.push_subscription import PushSubscription


class PushSubscriptionService(CrudService):
    model = PushSubscription


# Singleton instance
_service = PushSubscriptionService()


# Generic getter (for auto-generated routers)
def get_service() -> PushSubscriptionService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_push_subscription_service() -> PushSubscriptionService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
