from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.slusi_ingestion_run import SlusiIngestionRun


class SlusiIngestionRunService(CrudService):
    model = SlusiIngestionRun


# Singleton instance
_service = SlusiIngestionRunService()


# Generic getter (for auto-generated routers)
def get_service() -> SlusiIngestionRunService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_slusi_ingestion_run_service() -> SlusiIngestionRunService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
