"""
Amazon Cognito authentication service (Migrated to Firebase Authentication)
Handles user registration, authentication, and token management
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _mock_auth_allowed() -> bool:
    # The mock fallbacks skip password and token checks entirely, so they are only safe locally/in tests.
    return settings.ENVIRONMENT in ("development", "test", "testing")


def _require_mock_allowed(operation: str) -> None:
    if not _mock_auth_allowed():
        logger.error(
            f"{operation}: Firebase auth is not configured; refusing mock fallback in {settings.ENVIRONMENT}"
        )
        raise Exception(f"{operation} failed: authentication service is not configured")


class CognitoService:
    """Service for Firebase Authentication operations (renamed/compatible with CognitoService)"""

    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self._initialized = False
        self._init_firebase()
        self.client = None

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
            logger.info(
                "Firebase Admin SDK initialized successfully in CognitoService compatibility wrapper"
            )
        except Exception as e:
            logger.warning(
                f"Firebase Admin SDK initialization failed: {e}. Running in fallback/mock mode."
            )
            self._initialized = False

    def sign_up(
        self,
        username: str,
        password: str,
        email: str,
        phone_number: Optional[str],
        full_name: str,
        user_attributes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user in Firebase Auth / Mock Cognito Client
        """
        if self.client is not None:
            cognito_attrs = [
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": full_name},
            ]
            if phone_number:
                cognito_attrs.append({"Name": "phone_number", "Value": phone_number})
            try:
                res = self.client.sign_up(
                    ClientId="mock_client_id",
                    Username=username,
                    Password=password,
                    UserAttributes=cognito_attrs,
                )
                return {
                    "user_sub": res.get("UserSub"),
                    "user_confirmed": res.get("UserConfirmed", True),
                    "code_delivery_details": res.get("CodeDeliveryDetails"),
                }
            except Exception as e:
                logger.error(f"Mock sign_up error: {e}")
                raise Exception(f"Sign up failed: {str(e)}")

        if not self._initialized:
            _require_mock_allowed("Sign up")
            logger.info("Firebase Admin not initialized. Creating mock signup response.")
            return {
                "user_sub": f"mock-sub-{username}",
                "user_confirmed": True,
                "code_delivery_details": None,
            }
        try:
            from firebase_admin import auth

            user = auth.create_user(
                email=email, phone_number=phone_number, password=password, display_name=full_name
            )
            # Link attributes to custom claims
            if user_attributes:
                auth.set_custom_user_claims(user.uid, user_attributes)

            return {"user_sub": user.uid, "user_confirmed": True, "code_delivery_details": None}
        except Exception as e:
            logger.error(f"Firebase sign_up error: {e}")
            raise Exception(f"Sign up failed: {str(e)}")

    def confirm_sign_up(self, username: str, confirmation_code: str) -> bool:
        """
        Confirm user registration (verify email in Firebase / Mock Cognito Client)
        """
        if self.client is not None:
            try:
                self.client.confirm_sign_up(
                    ClientId="mock_client_id", Username=username, ConfirmationCode=confirmation_code
                )
                return True
            except Exception as e:
                logger.error(f"Mock confirm_sign_up error: {e}")
                raise Exception(f"Confirmation failed: {str(e)}")

        if not self._initialized:
            _require_mock_allowed("Confirmation")
            return True
        try:
            from firebase_admin import auth

            user = auth.get_user_by_email(username)
            auth.update_user(user.uid, email_verified=True)
            return True
        except Exception as e:
            logger.error(f"Firebase confirm_sign_up error: {e}")
            raise Exception(f"Confirmation failed: {str(e)}")

    def resend_confirmation_code(self, username: str) -> Dict[str, Any]:
        """
        Placeholder / Resend confirmation code
        """
        if self.client is not None:
            try:
                return self.client.resend_confirmation_code(
                    ClientId="mock_client_id", Username=username
                )
            except Exception as e:
                logger.error(f"Mock resend_confirmation_code error: {e}")
                raise Exception(f"Resend confirmation code failed: {str(e)}")
        return {}

    def sign_in(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and get tokens via Google Identity Toolkit REST API / Mock Cognito Client
        """
        if self.client is not None:
            try:
                res = self.client.initiate_auth(
                    ClientId="mock_client_id",
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={"USERNAME": username, "PASSWORD": password},
                )
                auth_res = res.get("AuthenticationResult", {})
                return {
                    "access_token": auth_res.get("AccessToken"),
                    "id_token": auth_res.get("IdToken"),
                    "refresh_token": auth_res.get("RefreshToken"),
                    "expires_in": auth_res.get("ExpiresIn", 3600),
                    "token_type": auth_res.get("TokenType", "Bearer"),
                }
            except Exception as e:
                logger.error(f"Mock sign_in error: {e}")
                raise Exception(f"Sign in failed: {str(e)}")

        api_key = os.getenv("FIREBASE_API_KEY")

        # Seeded e2e users all share E2E_PASSWORD, so wrong-password flows can be tested.
        if settings.E2E_ACTIVE and password != settings.E2E_PASSWORD:
            raise Exception("Sign in failed: INVALID_PASSWORD")

        if settings.E2E_ACTIVE or not api_key or settings.ENVIRONMENT == "development":
            _require_mock_allowed("Sign in")
            logger.info(
                "Firebase Web API Key not set or in dev mode. Returning mock token instantly."
            )
            return {
                "access_token": f"mock-token-{username}",
                "id_token": f"mock-token-{username}",
                "refresh_token": "mock-refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            }

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {"email": username, "password": password, "returnSecureToken": True}
        try:
            with httpx.Client() as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    error_msg = res.json().get("error", {}).get("message", "Authentication failed")
                    raise Exception(error_msg)
                data = res.json()
                return {
                    "access_token": data["idToken"],
                    "id_token": data["idToken"],
                    "refresh_token": data["refreshToken"],
                    "expires_in": int(data["expiresIn"]),
                    "token_type": "Bearer",
                }
        except Exception as e:
            logger.error(f"Firebase sign_in failed: {e}")
            raise Exception(f"Sign in failed: {str(e)}")

    def respond_to_mfa_challenge(
        self, username: str, session: str, mfa_code: str
    ) -> Dict[str, Any]:
        """
        Respond to MFA challenge (SMS verification code)
        """
        # Standalone Firebase handles MFA verification on frontend
        # For compatibility, returns mock tokens or completes verification
        return self.sign_in(username, "temp_password_or_fallback")

    def refresh_token(self, username: str, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh ID token using refresh token
        """
        if self.client is not None:
            try:
                res = self.client.initiate_auth(
                    ClientId="mock_client_id",
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    AuthParameters={"REFRESH_TOKEN": refresh_token},
                )
                auth_res = res.get("AuthenticationResult", {})
                return {
                    "access_token": auth_res.get("AccessToken"),
                    "id_token": auth_res.get("IdToken"),
                    "refresh_token": auth_res.get("RefreshToken") or refresh_token,
                    "expires_in": auth_res.get("ExpiresIn", 3600),
                }
            except Exception as e:
                logger.error(f"Mock refresh_token error: {e}")
                raise Exception(f"Token refresh failed: {str(e)}")

        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            _require_mock_allowed("Token refresh")
            return {"access_token": refresh_token, "id_token": refresh_token, "expires_in": 3600}
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        try:
            with httpx.Client() as client:
                res = client.post(url, data=payload)
                data = res.json()
                return {
                    "access_token": data["id_token"],
                    "id_token": data["id_token"],
                    "expires_in": int(data["expires_in"]),
                }
        except Exception as e:
            logger.error(f"Firebase token refresh failed: {e}")
            raise Exception(f"Token refresh failed: {str(e)}")

    def sign_out(self, access_token: str) -> bool:
        """
        Sign out user (revoke refresh tokens)
        """
        try:
            from firebase_admin import auth

            decoded = auth.verify_id_token(access_token)
            auth.revoke_refresh_tokens(decoded["uid"])
            logger.info("User logged out and tokens revoked successfully")
            return True
        except Exception:
            return True

    def forgot_password(self, username: str) -> Dict[str, Any]:
        """
        Initiate forgot password email flow
        """
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            return {}
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
        payload = {"requestType": "PASSWORD_RESET", "email": username}
        try:
            with httpx.Client() as client:
                client.post(url, json=payload)
            return {}
        except Exception as e:
            logger.error(f"Firebase forgot_password failed: {e}")
            raise Exception(f"Password reset failed: {str(e)}")

    def confirm_forgot_password(
        self, username: str, confirmation_code: str, new_password: str
    ) -> bool:
        """
        Confirm forgot password code (oobCode) and set new password
        """
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            return True
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={api_key}"
        payload = {"oobCode": confirmation_code, "newPassword": new_password}
        try:
            with httpx.Client() as client:
                res = client.post(url, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Firebase confirm_forgot_password failed: {e}")
            raise Exception(f"Password confirmation failed: {str(e)}")

    def change_password(
        self, access_token: str, previous_password: str, proposed_password: str
    ) -> bool:
        """
        Change user password
        """
        try:
            from firebase_admin import auth

            decoded = auth.verify_id_token(access_token)
            auth.update_user(decoded["uid"], password=proposed_password)
            logger.info("User changed password successfully")
            return True
        except Exception as e:
            logger.error(f"Firebase change_password failed: {e}")
            raise Exception(f"Password change failed: {str(e)}")

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user details from Firebase token
        """
        # Mock tokens impersonate users, so they must never work outside dev/test.
        if settings.ENVIRONMENT in ("development", "test", "testing") and (access_token.startswith("mock-") or access_token == "test-token"):
            username_or_email = "farmer@cropsense.ai"
            if access_token.startswith("mock-token-"):
                username_or_email = access_token.replace("mock-token-", "")
            elif access_token.startswith("mock-"):
                username_or_email = access_token.replace("mock-", "")

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
            except Exception as db_err:
                logger.error(f"Failed to query user for mock user get_user fallback: {db_err}")
            finally:
                db.close()

            if db_user:
                return {
                    "username": db_user.username,
                    "user_sub": db_user.cognito_user_id or db_user.firebase_id or f"mock-{username_or_email}",
                    "email": db_user.email,
                    "email_verified": True,
                    "phone_number": db_user.phone or "+919876543210",
                    "phone_verified": True,
                    "name": db_user.name,
                    "attributes": {},
                }
            return {
                "username": username_or_email,
                "user_sub": f"mock-{username_or_email}",
                "email": username_or_email,
                "email_verified": True,
                "phone_number": "+919876543210",
                "phone_verified": True,
                "name": username_or_email.split("@")[0].capitalize(),
                "attributes": {},
            }

        try:
            from firebase_admin import auth

            decoded = auth.verify_id_token(access_token)
            try:
                user = auth.get_user(decoded["uid"])
            except Exception as lookup_err:
                # No admin credentials (e.g. local dev): the verified token carries what we need.
                logger.warning(f"Firebase get_user unavailable, using token claims: {lookup_err}")
                return {
                    "username": decoded.get("email") or decoded["uid"],
                    "user_sub": decoded["uid"],
                    "email": decoded.get("email"),
                    "email_verified": decoded.get("email_verified", False),
                    "phone_number": decoded.get("phone_number"),
                    "phone_verified": decoded.get("phone_number") is not None,
                    "name": decoded.get("name") or "Firebase User",
                    "attributes": {},
                }
            return {
                "username": user.email or user.uid,
                "user_sub": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "phone_number": user.phone_number,
                "phone_verified": user.phone_number is not None,
                "name": user.display_name or "Firebase User",
                "attributes": user.custom_claims or {},
            }
        except Exception as e:
            if _mock_auth_allowed() and (
                access_token.startswith("mock-")
                or access_token == "test-token"
                or settings.ENVIRONMENT == "development"
            ):
                username_or_email = "puneetxp"
                if access_token.startswith("mock-token-"):
                    username_or_email = access_token.replace("mock-token-", "")
                elif access_token.startswith("mock-"):
                    username_or_email = access_token.replace("mock-", "")

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
                except Exception as db_err:
                    logger.error(f"Failed to query user for mock user get_user fallback: {db_err}")
                finally:
                    db.close()

                if db_user:
                    return {
                        "username": db_user.username,
                        "user_sub": db_user.cognito_user_id or db_user.firebase_id,
                        "email": db_user.email,
                        "email_verified": True,
                        "phone_number": db_user.phone,
                        "phone_verified": db_user.phone is not None,
                        "name": db_user.name,
                        "attributes": {},
                    }
                else:
                    uid = username_or_email
                    return {
                        "username": "test-farmer",
                        "user_sub": uid,
                        "email": "test@cropsense.ai",
                        "email_verified": True,
                        "phone_number": "+919999999999",
                        "phone_verified": True,
                        "name": "Test Farmer",
                        "attributes": {},
                    }
            logger.error(f"Firebase get_user failed: {e}")
            raise Exception(f"Get user failed: {str(e)}")

    def update_user_attributes(self, access_token: str, attributes: Dict[str, str]) -> bool:
        """
        Update user custom claims (attributes)
        """
        try:
            from firebase_admin import auth

            decoded = auth.verify_id_token(access_token)
            auth.set_custom_user_claims(decoded["uid"], attributes)
            return True
        except Exception as e:
            logger.error(f"Firebase update_user_attributes failed: {e}")
            raise Exception(f"Update failed: {str(e)}")

    def enable_mfa(self, access_token: str) -> bool:
        return True

    def disable_mfa(self, access_token: str) -> bool:
        return True

    def admin_delete_user(self, username: str) -> bool:
        """
        Delete a user from Firebase Auth (Admin)
        """
        if not self._initialized:
            _require_mock_allowed("Delete user")
            return True
        try:
            from firebase_admin import auth

            user = auth.get_user_by_email(username)
            auth.delete_user(user.uid)
            return True
        except Exception as e:
            logger.error(f"Firebase admin_delete_user failed: {e}")
            raise Exception(f"Delete failed: {str(e)}")


# Singleton instance
cognito_service = CognitoService()
