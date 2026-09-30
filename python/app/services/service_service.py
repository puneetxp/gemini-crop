from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.service import Service


class ServiceService(CrudService):
    model = Service


# Singleton instance
_service = ServiceService()


# Generic getter (for auto-generated routers)
def get_service() -> ServiceService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_service_service() -> ServiceService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
