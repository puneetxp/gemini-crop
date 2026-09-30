from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.livestock_marketplace_listing import LivestockMarketplaceListing


class LivestockMarketplaceListingService(CrudService):
    model = LivestockMarketplaceListing


# Singleton instance
_service = LivestockMarketplaceListingService()


# Generic getter (for auto-generated routers)
def get_service() -> LivestockMarketplaceListingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_livestock_marketplace_listing_service() -> LivestockMarketplaceListingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
