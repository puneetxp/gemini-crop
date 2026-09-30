from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.fertilizer_application import FertilizerApplication


class FertilizerApplicationService(CrudService):
    model = FertilizerApplication


# Singleton instance
_service = FertilizerApplicationService()


# Generic getter (for auto-generated routers)
def get_service() -> FertilizerApplicationService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_fertilizer_application_service() -> FertilizerApplicationService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
