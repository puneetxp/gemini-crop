from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.payment_milestone import PaymentMilestone


class PaymentMilestoneService(CrudService):
    model = PaymentMilestone


# Singleton instance
_service = PaymentMilestoneService()


# Generic getter (for auto-generated routers)
def get_service() -> PaymentMilestoneService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_payment_milestone_service() -> PaymentMilestoneService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
