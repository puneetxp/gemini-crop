from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.shc_state_district_code import ShcStateDistrictCode


class ShcStateDistrictCodeService(CrudService):
    model = ShcStateDistrictCode


# Singleton instance
_service = ShcStateDistrictCodeService()


# Generic getter (for auto-generated routers)
def get_service() -> ShcStateDistrictCodeService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_shc_state_district_code_service() -> ShcStateDistrictCodeService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
