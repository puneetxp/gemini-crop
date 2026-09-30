from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.opportunity_cost import OpportunityCost


class OpportunityCostService(CrudService):
    model = OpportunityCost


# Singleton instance
_service = OpportunityCostService()


# Generic getter (for auto-generated routers)
def get_service() -> OpportunityCostService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_opportunity_cost_service() -> OpportunityCostService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
