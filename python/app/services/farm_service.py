from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.farm import Farm


class FarmService(CrudService):
    model = Farm


# Singleton instance
_service = FarmService()


# Generic getter (for auto-generated routers)
def get_service() -> FarmService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_farm_service() -> FarmService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
