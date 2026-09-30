"""
Typed FastAPI dependencies for CropSense AI endpoints.
Provides CurrentUser, CurrentFarmer, CurrentAdmin, OptionalUser, get_db,
and typed Service dependencies for all business routes.
"""
from __future__ import annotations

from typing import Annotated, Any, Dict, Generator, Optional, Union

try:
    from fastapi import Depends
    from fastapi.security import HTTPAuthorizationCredentials
except ImportError:
    def Depends(dep: Any = None) -> Any:  # type: ignore
        return dep

    class HTTPAuthorizationCredentials:  # type: ignore
        def __init__(self, scheme: str = "Bearer", credentials: str = ""):
            self.scheme = scheme
            self.credentials = credentials

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session
    from app.core.database import get_async_db
    from app.core.database import get_db as get_sqlalchemy_db
except ImportError:
    Session = Any  # type: ignore
    AsyncSession = Any  # type: ignore

    def get_async_db():
        pass

    def get_sqlalchemy_db():
        pass


from app.core.auth import (
    get_current_active_user,
    get_current_admin,
    get_current_buyer,
    get_current_farmer,
    get_current_user,
    get_current_verified_user,
    get_optional_current_user,
    get_optional_user,
    security,
)
from app.core.db import DB as CoreDB
from app.orm.user import User


def get_db() -> Generator[Any, None, None]:
    """Dependency supplying database transaction or SQLAlchemy session."""
    try:
        from app.core.database import get_db as get_sa_db
        db_gen = get_sa_db()
        db = next(db_gen)
        try:
            yield db
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    except Exception:
        with CoreDB.transaction() as conn:
            yield conn


# Core Database Dependencies
DB = Annotated[Any, Depends(get_db)]
AsyncDB = Annotated[Any, Depends(get_async_db)]

# Authentication Dependencies
CurrentUser = Annotated[Any, Depends(get_current_active_user)]
VerifiedUser = Annotated[Any, Depends(get_current_verified_user)]
CurrentFarmer = Annotated[Any, Depends(get_current_farmer)]
CurrentBuyer = Annotated[Any, Depends(get_current_buyer)]
CurrentAdmin = Annotated[Any, Depends(get_current_admin)]
OptionalUser = Annotated[Optional[Any], Depends(get_optional_current_user)]
OptionalUserDict = Annotated[Optional[Dict[str, Any]], Depends(get_optional_current_user)]

# Security Dependencies
AuthCredentials = Annotated[HTTPAuthorizationCredentials, Depends(security)]


# Service Dependencies - Factories for dependency injection
def get_address_service():
    from app.services.address_service import AddressService
    return AddressService()


AddressSvc = Annotated[Any, Depends(get_address_service)]


def get_farm_service(db: DB = None):
    from app.services.farm_service import FarmService
    return FarmService(db)


FarmSvc = Annotated[Any, Depends(get_farm_service)]


def get_bedrock_service():
    from app.services.bedrock_service import bedrock_service
    return bedrock_service


BedrockSvc = Annotated[Any, Depends(get_bedrock_service)]


def get_marketplace_service(db: DB = None):
    from app.services.marketplace_service import MarketplaceService
    return MarketplaceService(db)


MarketplaceSvc = Annotated[Any, Depends(get_marketplace_service)]


def get_livestock_service(current_user: CurrentUser = None):
    from app.services.livestock_repository import LivestockRepository
    return LivestockRepository(current_user)


LivestockSvc = Annotated[Any, Depends(get_livestock_service)]


def get_ai_quota_service(db: DB = None):
    from app.services.ai_quota_service import AIQuotaService
    return AIQuotaService(db)


AIQuotaSvc = Annotated[Any, Depends(get_ai_quota_service)]
