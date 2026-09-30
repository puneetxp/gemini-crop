from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.soil_amendment import SoilAmendment


class SoilAmendmentService(CrudService):
    model = SoilAmendment


# Singleton instance
_service = SoilAmendmentService()


# Generic getter (for auto-generated routers)
def get_service() -> SoilAmendmentService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_soil_amendment_service() -> SoilAmendmentService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
