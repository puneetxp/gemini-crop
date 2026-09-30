from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.livestock import Livestock


class LivestockService(CrudService):
    model = Livestock


# Singleton instance
_service = LivestockService()


# Generic getter (for auto-generated routers)
def get_service() -> LivestockService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_livestock_service() -> LivestockService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
