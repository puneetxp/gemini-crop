from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.buyer_interest import BuyerInterest


class BuyerInterestService(CrudService):
    model = BuyerInterest


# Singleton instance
_service = BuyerInterestService()


# Generic getter (for auto-generated routers)
def get_service() -> BuyerInterestService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_buyer_interest_service() -> BuyerInterestService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
