from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.breeding_record import BreedingRecord


class BreedingRecordService(CrudService):
    model = BreedingRecord


# Singleton instance
_service = BreedingRecordService()


# Generic getter (for auto-generated routers)
def get_service() -> BreedingRecordService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_breeding_record_service() -> BreedingRecordService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
