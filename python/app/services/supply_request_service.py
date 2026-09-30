from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.supply_request import SupplyRequest


class SupplyRequestService(CrudService):
    model = SupplyRequest


# Singleton instance
_service = SupplyRequestService()


# Generic getter (for auto-generated routers)
def get_service() -> SupplyRequestService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_supply_request_service() -> SupplyRequestService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
