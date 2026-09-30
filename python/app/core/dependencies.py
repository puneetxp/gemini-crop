from typing import Annotated, Any, Dict, Optional, Union

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.auth import (
    get_current_active_user,
    get_current_admin,
    get_current_buyer,
    get_current_farmer,
    get_current_verified_user,
    get_optional_current_user,
    security,
)
from app.core.database import get_async_db, get_db
from app.orm.user import User
from app.services.address_service import AddressService
from app.services.ai_quota_service import AIQuotaService
from app.services.bedrock_service import BedrockService
from app.services.farm_service import FarmService
from app.services.livestock_service import LivestockService  # noqa: F401 (kept for importers)
from app.services.livestock_repository import LivestockRepository
from app.services.marketplace_service import MarketplaceService

# Core Database Dependency
# Cmd+Click Session to go to SQLAlchemy, or use this in Annotated
DB = Annotated[Session, Depends(get_db)]
AsyncDB = Annotated[AsyncSession, Depends(get_async_db)]

# Authentication Dependencies
# Cmd+Click User to go to the ORM model
CurrentUser = Annotated[User, Depends(get_current_active_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
CurrentFarmer = Annotated[User, Depends(get_current_farmer)]
CurrentBuyer = Annotated[User, Depends(get_current_buyer)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]
OptionalUserDict = Annotated[Optional[Dict[str, Any]], Depends(get_optional_current_user)]

# Security Dependencies
AuthCredentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


# Service Dependencies - Explicit factories for premium IDE support
def get_address_service() -> AddressService:
    return AddressService()


AddressSvc = Annotated[AddressService, Depends(get_address_service)]


def get_farm_service(db: DB) -> FarmService:
    return FarmService(db)


FarmSvc = Annotated[FarmService, Depends(get_farm_service)]


def get_bedrock_service() -> BedrockService:
    # Use the singleton instance if available, or create new one
    from app.services.bedrock_service import bedrock_service

    return bedrock_service


BedrockSvc = Annotated[BedrockService, Depends(get_bedrock_service)]


def get_marketplace_service(db: DB) -> MarketplaceService:
    return MarketplaceService(db)


MarketplaceSvc = Annotated[MarketplaceService, Depends(get_marketplace_service)]


def get_livestock_service(current_user: CurrentUser) -> LivestockRepository:
    # The generated LivestockService takes no db; the router's get_by_id/list/... API
    # lives in LivestockRepository, scoped to the signed-in farmer
    return LivestockRepository(current_user)


LivestockSvc = Annotated[LivestockRepository, Depends(get_livestock_service)]


def get_ai_quota_service(db: DB) -> AIQuotaService:
    return AIQuotaService(db)


AIQuotaSvc = Annotated[AIQuotaService, Depends(get_ai_quota_service)]
