from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.marketplace_listing import MarketplaceListing


class MarketplaceListingService(CrudService):
    model = MarketplaceListing


# Singleton instance
_service = MarketplaceListingService()


# Generic getter (for auto-generated routers)
def get_service() -> MarketplaceListingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_marketplace_listing_service() -> MarketplaceListingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
