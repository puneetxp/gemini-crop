from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.soil_test_result import SoilTestResult


class SoilTestResultService(CrudService):
    model = SoilTestResult


# Singleton instance
_service = SoilTestResultService()


# Generic getter (for auto-generated routers)
def get_service() -> SoilTestResultService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_soil_test_result_service() -> SoilTestResultService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
