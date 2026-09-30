"""
Firebase Authentication and JWT validation module for CropSense AI.
Handles Firebase token verification, fallback lookup by firebase_id,
E2E mock tokens (mock-token-<email>), and FastAPI user dependencies.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from fastapi import Depends, HTTPException, Security, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except ImportError:
    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int = 400, detail: str = "", headers: Optional[Dict[str, str]] = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class status:  # type: ignore
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403
        HTTP_429_TOO_MANY_REQUESTS = 429

    def Depends(dep: Any = None) -> Any:  # type: ignore
        return dep

    def Security(dep: Any = None) -> Any:  # type: ignore
        return dep

    class HTTPBearer:  # type: ignore
        def __init__(self, auto_error: bool = False):
            self.auto_error = auto_error

    class HTTPAuthorizationCredentials:  # type: ignore
        def __init__(self, scheme: str = "Bearer", credentials: str = ""):
            self.scheme = scheme
            self.credentials = credentials

from app.core.config import settings
from app.core.db import DB

logger = logging.getLogger("cropsense.auth")

security_bearer = HTTPBearer(auto_error=False)


class FirebaseTokenValidator:
    """Validator for Firebase Auth ID Tokens."""

    _initialized: bool = False

    @classmethod
    def _init_firebase(cls) -> None:
        if cls._initialized:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                if settings.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                else:
                    firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
            cls._initialized = True
        except Exception as err:
            logger.warning("Firebase Admin SDK not initialized: %s", err)

    @classmethod
    def verify_token(cls, token: str, token_use: str = "access") -> Dict[str, Any]:
        """Verify Firebase token or mock token and return decoded claims."""
        # E2E / Test Mock Token Handling
        if token.startswith("mock-token-") or settings.E2E_ACTIVE:
            email = token.replace("mock-token-", "") if token.startswith("mock-token-") else "farmer@cropsense.ai"
            return {
                "uid": f"mock-{email}",
                "email": email,
                "name": email.split("@")[0].capitalize(),
                "email_verified": True,
            }

        cls._init_firebase()
        try:
            from firebase_admin import auth as fb_auth

            decoded = fb_auth.verify_id_token(token)
            return decoded
        except Exception as err:
            logger.warning("Firebase ID token verification failed: %s", err)
            # In local debug mode without live internet, support fallback
            if settings.DEBUG:
                return {
                    "uid": "debug-user-1",
                    "email": "farmer@cropsense.ai",
                    "name": "Dev Farmer",
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


def resolve_user_from_db(claims: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve full user profile from database using email or firebase_id/google_id."""
    uid = claims.get("uid") or claims.get("sub")
    email = claims.get("email")

    user_row = None
    if email:
        user_row = DB.raw("SELECT * FROM users WHERE email = %(email)s LIMIT 1", {"email": email}).exe().first()

    if not user_row and uid:
        user_row = (
            DB.raw(
                "SELECT * FROM users WHERE google_id = %(uid)s OR id::text = %(uid)s LIMIT 1",
                {"uid": uid},
            )
            .exe()
            .first()
        )

    # Auto-provision user record in local development / testing if not found
    if not user_row and (settings.DEBUG or settings.E2E_ACTIVE):
        name = claims.get("name") or (email.split("@")[0] if email else "User")
        user_row = (
            DB.raw(
                """
                INSERT INTO users (name, email, google_id, enable)
                VALUES (%(name)s, %(email)s, %(google_id)s, 1)
                RETURNING *
                """,
                {"name": name, "email": email or f"{uid}@cropsense.ai", "google_id": uid},
            )
            .exe()
            .first()
        )

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user profile not registered in CropSense system",
        )

    user_id = user_row["id"]

    # Fetch active roles
    roles: List[str] = []
    role_rows = (
        DB.raw(
            """
            SELECT r.name FROM roles r
            JOIN active_roles ar ON r.id = ar.role_id
            WHERE ar.user_id = %(uid)s
            """,
            {"uid": user_id},
        )
        .exe()
        .rows
    )

    if role_rows:
        roles = [r["name"] for r in role_rows]
    else:
        roles = ["farmer"]  # Default application role

    user_data = dict(user_row)
    user_data["roles"] = roles
    user_data["role"] = roles[0] if roles else "farmer"
    return user_data


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> Dict[str, Any]:
    """FastAPI dependency to extract and authenticate current user."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = FirebaseTokenValidator.verify_token(auth.credentials)
    return resolve_user_from_db(claims)


async def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> Optional[Dict[str, Any]]:
    """FastAPI dependency for optional authentication."""
    if not auth or not auth.credentials:
        return None
    try:
        claims = FirebaseTokenValidator.verify_token(auth.credentials)
        return resolve_user_from_db(claims)
    except Exception:
        return None


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """FastAPI dependency ensuring account is active."""
    if current_user.get("enable") == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def get_current_farmer(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """FastAPI dependency restricting endpoint to farmers or administrators."""
    roles = current_user.get("roles", [])
    if "farmer" not in roles and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmer role required to access this resource",
        )
    return current_user


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """FastAPI dependency restricting endpoint to administrators."""
    roles = current_user.get("roles", [])
    if "admin" not in roles and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


async def get_current_buyer(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """FastAPI dependency restricting endpoint to buyers or administrators."""
    roles = current_user.get("roles", [])
    role = current_user.get("role", "")
    if "buyer" not in roles and role != "buyer" and "admin" not in roles and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer role required to access this resource",
        )
    return current_user


async def get_current_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Dependency to get current verified user."""
    is_verified = (
        current_user.get("is_verified", True)
        if isinstance(current_user, dict)
        else getattr(current_user, "is_verified", True)
    )
    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please verify your email or phone number.",
        )
    return current_user


def require_role(allowed_roles: List[str]):
    """Dependency factory checking user role."""
    async def role_checker(current_user: Any = Depends(get_current_active_user)) -> Any:
        roles = []
        if isinstance(current_user, dict):
            roles = current_user.get("roles", [current_user.get("role", "farmer")])
            user_type = current_user.get("user_type", current_user.get("role", "farmer"))
        else:
            roles = getattr(current_user, "roles", [getattr(current_user, "role", "farmer")])
            user_type = getattr(current_user, "user_type", getattr(current_user, "role", "farmer"))

        if "admin" in roles or user_type == "admin":
            return current_user

        if any(r in allowed_roles for r in roles) or user_type in allowed_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
        )
    return role_checker


security = security_bearer
token_validator = FirebaseTokenValidator()
get_current_user_from_token = get_current_user
get_optional_current_user = get_optional_user


def extract_token_claims(token: str) -> Dict[str, Any]:
    """Extract claims without signature verification."""
    try:
        from jose import jwt
        return jwt.get_unverified_claims(token)
    except Exception:
        return {}

