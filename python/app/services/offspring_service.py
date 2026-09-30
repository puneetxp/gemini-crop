from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.offspring import Offspring


class OffspringService(CrudService):
    model = Offspring


# Singleton instance
_service = OffspringService()


# Generic getter (for auto-generated routers)
def get_service() -> OffspringService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_offspring_service() -> OffspringService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
