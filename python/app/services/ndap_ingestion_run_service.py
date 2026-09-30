from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.ndap_ingestion_run import NdapIngestionRun


class NdapIngestionRunService(CrudService):
    model = NdapIngestionRun


# Singleton instance
_service = NdapIngestionRunService()


# Generic getter (for auto-generated routers)
def get_service() -> NdapIngestionRunService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_ndap_ingestion_run_service() -> NdapIngestionRunService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
