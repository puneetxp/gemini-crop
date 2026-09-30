from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.transport_provider import TransportProvider


class TransportProviderService(CrudService):
    model = TransportProvider


# Singleton instance
_service = TransportProviderService()


# Generic getter (for auto-generated routers)
def get_service() -> TransportProviderService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_transport_provider_service() -> TransportProviderService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
