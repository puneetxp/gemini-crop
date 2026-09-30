from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.soil_test import SoilTest


class SoilTestService(CrudService):
    model = SoilTest


# Singleton instance
_service = SoilTestService()


# Generic getter (for auto-generated routers)
def get_service() -> SoilTestService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_soil_test_service() -> SoilTestService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
