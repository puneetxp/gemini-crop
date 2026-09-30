from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.veterinarian import Veterinarian


class VeterinarianService(CrudService):
    model = Veterinarian


# Singleton instance
_service = VeterinarianService()


# Generic getter (for auto-generated routers)
def get_service() -> VeterinarianService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_veterinarian_service() -> VeterinarianService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
