from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.livestock_listing import LivestockListing


class LivestockListingService(CrudService):
    model = LivestockListing


# Singleton instance
_service = LivestockListingService()


# Generic getter (for auto-generated routers)
def get_service() -> LivestockListingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_livestock_listing_service() -> LivestockListingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
