from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.supply_match import SupplyMatch


class SupplyMatchService(CrudService):
    model = SupplyMatch


# Singleton instance
_service = SupplyMatchService()


# Generic getter (for auto-generated routers)
def get_service() -> SupplyMatchService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_supply_match_service() -> SupplyMatchService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
