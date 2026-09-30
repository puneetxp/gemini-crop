from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.ndap_downloaded_file import NdapDownloadedFile


class NdapDownloadedFileService(CrudService):
    model = NdapDownloadedFile


# Singleton instance
_service = NdapDownloadedFileService()


# Generic getter (for auto-generated routers)
def get_service() -> NdapDownloadedFileService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_ndap_downloaded_file_service() -> NdapDownloadedFileService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
