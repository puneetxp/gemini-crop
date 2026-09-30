"""
Authentication and authorization utilities
JWT token validation with Amazon Cognito
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.orm.user import User

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class FirebaseTokenValidator:
    """Validate JWT tokens from Firebase Authentication"""

    def __init__(self):
        self.project_id = settings.FIREBASE_PROJECT_ID
        self._initialized = False
        self._init_firebase()

    def _init_firebase(self):
        import firebase_admin
        from firebase_admin import credentials

        if settings.E2E_ACTIVE:
            logger.warning("E2E mode: Firebase disabled, using mock auth against the e2e database")
            return
        try:
            if not firebase_admin._apps:
                # An explicit projectId lets ID-token verification work even without Google
                # credentials (local dev); only admin calls such as create_user need them.
                options = {"projectId": settings.FIREBASE_PROJECT_ID}
                if settings.GOOGLE_APPLICATION_CREDENTIALS:
                    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
                    firebase_admin.initialize_app(cred, options)
                else:
                    try:
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred, options)
                    except Exception:
                        # Fallback for local development without default credentials
                        firebase_admin.initialize_app(options=options)
            self._initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.warning(
                f"Firebase Admin SDK initialization failed: {e}. Auth will run in fallback/mock mode."
            )
            self._initialized = False

    def verify_token(self, token: str, token_use: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token from Firebase
        """
        # Mock/test tokens let anyone impersonate any user, so they must never work outside dev/test.
        non_production = settings.ENVIRONMENT in ("development", "test", "testing")
        if non_production and (
            not self._initialized
            or token.startswith("mock-")
            or token == "test-token"
            or settings.ENVIRONMENT == "development"
        ):
            logger.info("Bypassing token verification (using mock/test token)")
            # Extract standard test UID or use default
            username_or_email = "puneetxp"
            if token.startswith("mock-token-"):
                username_or_email = token.replace("mock-token-", "")
            elif token.startswith("mock-"):
                username_or_email = token.replace("mock-", "")
            logger.info(f"DEBUG MOCK AUTH: token={token} -> username_or_email={username_or_email}")

            # Find the user's real cognito_user_id from the database
            from app.core.database import SessionLocal
            from app.orm.user_sqlalchemy import User as SqlUser

            db = SessionLocal()
            db_user = None
            try:
                db_user = (
                    db.query(SqlUser)
                    .filter(
                        (SqlUser.username == username_or_email)
                        | (SqlUser.email == username_or_email)
                    )
                    .first()
                )
            except Exception as e:
                logger.error(f"Failed to query user for mock token fallback: {e}")
            finally:
                db.close()

            if db_user:
                logger.info(f"DEBUG MOCK AUTH: found db_user={db_user.username} for token={token}")
                return {
                    "uid": db_user.cognito_user_id,
                    "username": db_user.username,
                    "sub": db_user.cognito_user_id,
                    "email": db_user.email,
                    "email_verified": True,
                    "phone_number": db_user.phone or "+919999999999",
                    "token_use": token_use,
                }
            else:
                logger.warning(
                    f"DEBUG MOCK AUTH: NO db_user found for username_or_email={username_or_email} (token={token})"
                )
                uid = username_or_email
                return {
                    "uid": uid,
                    "username": "test-farmer",
                    "sub": uid,
                    "email": "test@cropsense.ai",
                    "email_verified": True,
                    "phone_number": "+919999999999",
                    "token_use": token_use,
                }

        if not self._initialized:
            logger.error("Firebase Admin SDK is not initialized; rejecting token")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

        try:
            from firebase_admin import auth

            # Firebase ID tokens correspond to Cognito ID/access tokens
            decoded_token = auth.verify_id_token(token)
            # Standardize claims to match existing codebase expectations:
            # - Cognito 'sub' -> Firebase 'uid'
            # - Cognito 'username' -> Firebase 'uid'
            decoded_token["sub"] = decoded_token.get("uid")
            decoded_token["username"] = decoded_token.get("uid") or decoded_token.get("email")
            decoded_token["token_use"] = token_use
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
            )


# Singleton instance
token_validator = FirebaseTokenValidator()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user_from_token)):
            return {"user": current_user.full_name}
    """
    token = credentials.credentials

    # Verify token
    claims = token_validator.verify_token(token, token_use="access")

    # Get user from database
    cognito_username = claims.get("username")
    cognito_user_id = claims.get("sub")

    if not cognito_username or not cognito_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    # Find user in database using custom ORM
    query = User.where({"cognito_user_id": [cognito_user_id]})
    result = query.get()

    # Fallback to firebase_id if not found
    if not result or not result.items or len(result.items) == 0:
        query = User.where({"firebase_id": [cognito_user_id]})
        result = query.get()

    if not result or not result.items or len(result.items) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Convert dict to User object
    user_data = result.items[0]
    user = User()
    for key, value in user_data.items():
        setattr(user, key, value)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Temporary demo accounts stop working at the end of their lifetime (then get deleted)
    from app.services.demo_accounts import is_expired

    if is_expired(getattr(user, "email", None), getattr(user, "created_at", None)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demo session expired")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user_from_token),
) -> User:
    """
    Dependency to get current active user
    Ensures user is active and verified
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return current_user


async def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to get current verified user
    Ensures user has verified their email/phone
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified. Please verify your email or phone number.",
        )

    return current_user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory to check user role

    Usage:
        @app.get("/admin")
        async def admin_route(
            current_user: User = Depends(require_role(["admin"]))
        ):
            return {"message": "Admin access granted"}
    """

    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.user_type not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


# Role-specific dependencies
async def get_current_farmer(current_user: User = Depends(require_role(["farmer"]))) -> User:
    """Dependency to ensure current user is a farmer"""
    return current_user


async def get_current_buyer(current_user: User = Depends(require_role(["buyer"]))) -> User:
    """Dependency to ensure current user is a buyer"""
    return current_user


async def get_current_admin(current_user: User = Depends(require_role(["admin"]))) -> User:
    """Dependency to ensure current user is an admin"""
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to get current user if token is provided, otherwise None
    Useful for endpoints that work with or without authentication

    Usage:
        @app.get("/items")
        async def get_items(current_user: Optional[User] = Depends(get_optional_current_user)):
            if current_user:
                # Return personalized items
            else:
                # Return public items
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        claims = token_validator.verify_token(token, token_use="access")
        cognito_user_id = claims.get("sub")

        if not cognito_user_id:
            raise HTTPException(status_code=500, detail="DEBUG AUTH: Token sub claim missing")

        print(f"DEBUG AUTH: querying User for sub={cognito_user_id}")
        query = User.where({"cognito_user_id": [cognito_user_id]})
        result = query.get()

        # Fallback to firebase_id if not found
        if not result or not result.items or len(result.items) == 0:
            query = User.where({"firebase_id": [cognito_user_id]})
            result = query.get()

        if result and result.items and len(result.items) > 0:
            user_data = result.items[0]
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)

            if not user.is_active:
                raise HTTPException(
                    status_code=500, detail=f"DEBUG AUTH: user INACTIVE. sub={cognito_user_id}"
                )

            return user
        else:
            raise HTTPException(
                status_code=500, detail=f"DEBUG AUTH: NO user found. sub={cognito_user_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_info = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"DEBUG AUTH ERROR: {str(e)}\n{error_info}")

    return None


def extract_token_claims(token: str) -> Dict[str, Any]:
    """
    Extract claims from token without full verification
    Useful for debugging or logging

    Args:
        token: JWT token

    Returns:
        Token claims
    """
    try:
        return jwt.get_unverified_claims(token)
    except:
        return {}


# Alias for backward compatibility
get_current_user = get_current_user_from_token
