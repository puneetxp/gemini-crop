"""
Authentication API endpoints
Handles user registration, sign-in, MFA, password reset
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.auth import token_validator
from app.core.database import get_db
from app.orm.user_sqlalchemy import User
from app.schemas.auth import (
    ConfirmForgotPasswordRequest,
    ConfirmSignUpRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleSignInRequest,
    MessageResponse,
    MFAChallengeResponse,
    MFAVerifyRequest,
    RefreshTokenRequest,
    ResendCodeRequest,
    SignInRequest,
    SignInResponse,
    SignUpRequest,
    SignUpResponse,
)
from app.schemas.user import UserCreate
from app.services.cognito_service import cognito_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate Bearer token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required"
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
        )

    return parts[1]


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(request: SignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user with Amazon Cognito

    - **username**: Unique username (3-50 characters)
    - **password**: Password (minimum 8 characters)
    - **email**: Valid email address
    - **phone_number**: Phone number in format +919876543210
    - **full_name**: User's full name
    - **user_type**: User type (farmer, buyer, admin)

    Returns user_sub and confirmation status.
    User will receive verification code via email/SMS.
    """
    try:
        # 1. Check if email already exists
        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            if not existing_email.is_verified:
                # User exists but not verified - ALLOW REWRITE (delete and recreate)
                logger.info(f"Unverified email {request.email} found. Deleting for rewrite.")
                try:
                    # Clean up Cognito first
                    cognito_service.admin_delete_user(request.email)
                except Exception as ce:
                    logger.warning(
                        f"Could not delete unverified Cognito user {request.email}: {ce}"
                    )

                # Delete from DB
                db.delete(existing_email)
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered and verified. Please sign in instead.",
                )

        # 2. Check if username already exists
        existing_username = db.query(User).filter(User.username == request.username).first()
        if existing_username:
            if not existing_username.is_verified:
                logger.info(f"Unverified username {request.username} found. Deleting for rewrite.")
                try:
                    # If email is different, we might not know the Cognito username to delete
                    # But in our system, Cognito username = email
                    cognito_service.admin_delete_user(existing_username.email)
                except Exception as ce:
                    logger.warning(
                        f"Could not delete unverified Cognito user for username {request.username}: {ce}"
                    )

                db.delete(existing_username)
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists. Please choose a different username.",
                )

        # 3. Check if phone number already exists
        existing_phone = (
            db.query(User).filter(User.phone == request.phone_number).first()
            if request.phone_number
            else None
        )
        if existing_phone:
            if not existing_phone.is_verified:
                logger.info(f"Unverified phone {request.phone_number} found. Deleting for rewrite.")
                try:
                    cognito_service.admin_delete_user(existing_phone.email)
                except Exception as ce:
                    logger.warning(
                        f"Could not delete unverified Cognito user for phone {request.phone_number}: {ce}"
                    )

                db.delete(existing_phone)
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already registered. Please sign in or use forgot password.",
                )

        try:
            # Don't send username as custom attribute to Cognito
            # We'll store it in our database instead
            cognito_response = cognito_service.sign_up(
                username=request.email,  # Use email as Cognito username
                password=request.password,
                email=request.email,
                phone_number=request.phone_number,
                full_name=request.full_name,
                user_attributes=None,  # No custom attributes
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Cognito sign up error: {error_msg}")

            # Handle case where user exists in Cognito but not in our database
            if "UsernameExistsException" in error_msg or "User already exists" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered. Please sign in or use forgot password if you don't remember your credentials.",
                )

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Create user record in database
        address_line = request.address_line

        db_user = User(
            username=request.username,  # Display username
            cognito_user_id=cognito_response["user_sub"],
            email=request.email,
            phone=request.phone_number,
            name=request.full_name,
            user_type=request.user_type,
            is_verified=int(cognito_response["user_confirmed"]),
            is_active=1,
            # Address fields (optional)
            latitude=request.latitude,
            longitude=request.longitude,
            pincode=request.pincode,
            state=request.state,
            district=request.district,
            village=request.village,
            address_line=address_line,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User {request.username} (email: {request.email}) registered successfully")

        return SignUpResponse(
            user_sub=cognito_response["user_sub"],
            user_confirmed=cognito_response["user_confirmed"],
            message="User registered successfully. Please verify your email/phone. Use your email to sign in.",
            code_delivery_details=cognito_response.get("code_delivery_details"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign up error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/confirm-signup", response_model=MessageResponse)
async def confirm_sign_up(request: ConfirmSignUpRequest, db: Session = Depends(get_db)):
    """
    Confirm user registration with verification code

    - **username**: Username or email address
    - **confirmation_code**: 6-digit verification code received via email/SMS
    """
    try:
        # If username is not an email, look up the email
        email_for_cognito = request.username
        if "@" not in request.username:
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                email_for_cognito = user.email

        # Confirm in Cognito using email
        cognito_service.confirm_sign_up(
            username=email_for_cognito, confirmation_code=request.confirmation_code
        )

        # Update user verification status in database
        user = (
            db.query(User)
            .filter((User.email == email_for_cognito) | (User.username == request.username))
            .first()
        )
        if user:
            user.is_verified = 1
            db.commit()

        logger.info(f"User {request.username} confirmed successfully")

        return MessageResponse(
            message="Account verified successfully. You can now sign in with your email.",
            success=True,
        )

    except Exception as e:
        logger.error(f"Confirm sign up error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: ConfirmSignUpRequest, db: Session = Depends(get_db)):
    """
    Alias for confirm-signup to match frontend expectations.
    Verify user email with verification code (OTP).
    """
    return await confirm_sign_up(request, db)


@router.post("/resend-code", response_model=MessageResponse)
async def resend_confirmation_code(request: ResendCodeRequest):
    """
    Resend verification code to user

    - **username**: Username to resend code to
    """
    try:
        code_delivery = cognito_service.resend_confirmation_code(request.username)

        return MessageResponse(
            message=f"Verification code sent to {code_delivery.get('Destination', 'your registered contact')}",
            success=True,
        )

    except Exception as e:
        logger.error(f"Resend code error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(request: ResendCodeRequest):
    """
    Alias for resend-code to match frontend expectations.
    Resend verification code to user.
    """
    return await resend_confirmation_code(request)


@router.post("/signin", response_model=SignInResponse | MFAChallengeResponse)
async def sign_in(request: SignInRequest, db: Session = Depends(get_db)):
    """
    Sign in user with username/email and password

    - **username**: Username or email address
    - **password**: Password

    Returns JWT tokens if successful, or MFA challenge if MFA is enabled.
    """
    try:
        # Check if username is an email, if so, use it directly for Cognito
        # Otherwise, look up the email from the database
        email_for_cognito = request.username

        if "@" not in request.username:
            # Username provided, look up email
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                email_for_cognito = user.email
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Authenticate with Cognito using email
        auth_response = cognito_service.sign_in(
            username=email_for_cognito, password=request.password
        )

        # Handle MFA challenge
        if auth_response.get("challenge") == "SMS_MFA":
            return MFAChallengeResponse(
                challenge="SMS_MFA",
                session=auth_response["session"],
                message="MFA code sent to your phone. Please verify.",
            )

        # Handle new password required
        if auth_response.get("challenge") == "NEW_PASSWORD_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="New password required. Please reset your password.",
            )

        # Get user from database using email or username
        user = (
            db.query(User)
            .filter((User.email == email_for_cognito) | (User.username == request.username))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database"
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        logger.info(f"User {request.username} signed in successfully")

        return SignInResponse(
            access_token=auth_response["access_token"],
            id_token=auth_response["id_token"],
            refresh_token=auth_response["refresh_token"],
            expires_in=auth_response["expires_in"],
            token_type=auth_response["token_type"],
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "user_type": user.user_type,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign in error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def _unique_username(db: Session, seed: str) -> str:
    base = seed.split("@")[0].lstrip("+")[:90] or "user"
    candidate, n = base, 1
    while db.query(User).filter(User.username == candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate


class DemoSignInRequest(BaseModel):
    lang: str = Field("en", max_length=10)


@router.post("/demo")
async def demo_sign_in(body: DemoSignInRequest, request: Request, db: Session = Depends(get_db)):
    """
    Sign in to a new temporary demo farmer account with a sample farm.

    Each call creates a separate account, so visitors never share data. The session refreshes like a
    normal sign-in until DEMO_TTL_HOURS after creation; then the account and all its data are deleted.
    Returns the same tokens as /auth/signin plus `demo_expires_at`.
    """
    from app.core.rate_limiter import client_ip
    from app.services import demo_accounts

    if not settings.DEMO_LOGIN_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo sign-in is disabled")
    if not demo_accounts.allow_ip(client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many demo accounts from this network. Please try again in an hour.",
        )
    try:
        lang = body.lang if body.lang.isalpha() else "en"
        return demo_accounts.create_demo_account(db, lang=lang)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Demo sign-in failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not start a demo session. Please try again.",
        )


@router.post("/firebase", response_model=SignInResponse)
@router.post("/google", response_model=SignInResponse)
async def firebase_sign_in(request: GoogleSignInRequest, db: Session = Depends(get_db)):
    """
    Sign in with any Firebase provider (Google, email/password, phone OTP). The client signs in
    with the Firebase SDK and sends the resulting ID token; the user record lives in Postgres and
    is created on first sign-in. Phone is optional for Google/email users.
    """
    claims = token_validator.verify_token(request.id_token, token_use="id")
    uid = claims.get("uid") or claims.get("sub")
    email = claims.get("email")
    phone = claims.get("phone_number")
    if not uid or not (email or phone):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account has no email or phone"
        )
    who = email or phone

    try:
        user = (
            db.query(User).filter((User.firebase_id == uid) | (User.cognito_user_id == uid)).first()
        )
        if not user:
            # Link an account created earlier with the same email or phone.
            user = db.query(User).filter(User.email == email).first() if email else None
            user = user or (db.query(User).filter(User.phone == phone).first() if phone else None)
            if user:
                user.firebase_id = uid
        if user:
            # A phone sign-up's name is just the number; take the provider's name/email when they arrive.
            if claims.get("name") and (not user.name or user.name == user.phone):
                user.name = claims["name"]
            if email and not user.email:
                user.email = email
        if not user:
            user = User(
                username=_unique_username(db, who),
                name=claims.get("name") or who.split("@")[0],
                email=email,
                phone=phone,
                firebase_id=uid,
                cognito_user_id=uid,
                user_type="farmer",
                is_verified=1 if (claims.get("email_verified") or phone) else 0,
                is_active=1,
            )
            db.add(user)
            logger.info(f"Created user {who} via Firebase sign-in")
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"Firebase sign-in failed for {who}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not sign in"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return SignInResponse(
        access_token=request.id_token,
        id_token=request.id_token,
        refresh_token=request.refresh_token or "",
        expires_in=3600,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "user_type": user.user_type,
        },
    )


@router.post("/verify-mfa", response_model=SignInResponse)
async def verify_mfa(request: MFAVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify MFA code and complete sign-in

    - **username**: Username
    - **session**: Session token from sign-in response
    - **mfa_code**: 6-digit MFA code received via SMS
    """
    try:
        # Verify MFA with Cognito
        auth_response = cognito_service.respond_to_mfa_challenge(
            username=request.username, session=request.session, mfa_code=request.mfa_code
        )

        # Get user from database
        user = db.query(User).filter(User.username == request.username).first()

        logger.info(f"User {request.username} completed MFA verification")

        return SignInResponse(
            access_token=auth_response["access_token"],
            id_token=auth_response["id_token"],
            refresh_token=auth_response["refresh_token"],
            expires_in=auth_response["expires_in"],
            token_type="Bearer",
            user=(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "name": user.name,
                    "user_type": user.user_type,
                }
                if user
                else None
            ),
        )

    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=SignInResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token

    - **username**: Username
    - **refresh_token**: Refresh token from sign-in
    """
    try:
        # Determine the cognito sub UUID for the user to properly verify the SECRET_HASH on refresh
        if "@" not in request.username:
            user = db.query(User).filter(User.username == request.username).first()
        else:
            user = db.query(User).filter(User.email == request.username).first()

        if user and user.cognito_user_id:
            username_for_refresh = user.cognito_user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found or missing Cognito ID"
            )

        # Refresh token with Cognito using the SUB
        auth_response = cognito_service.refresh_token(
            username=username_for_refresh, refresh_token=request.refresh_token
        )

        logger.info(f"Token refreshed for user {request.username}")

        return SignInResponse(
            access_token=auth_response["access_token"],
            id_token=auth_response["id_token"],
            refresh_token=request.refresh_token,  # Refresh token doesn't change
            expires_in=auth_response["expires_in"],
            token_type="Bearer",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh-token", response_model=SignInResponse)
async def refresh_token_alias(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token (alias endpoint)

    This is an alias for /refresh to maintain compatibility with frontend.

    - **username**: Username
    - **refresh_token**: Refresh token from sign-in
    """
    return await refresh_token(request, db)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate forgot password flow

    - **username**: Username or email address

    Sends verification code to user's registered email/phone.
    """
    try:
        # Determine if username is an email or needs lookup
        email_for_cognito = request.username

        if "@" not in request.username:
            # Username provided, look up email from database
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                email_for_cognito = user.email
                logger.info(f"User found in DB - Username: {user.username}, Email: {user.email}")
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Send password reset code using email
        code_delivery = cognito_service.forgot_password(email_for_cognito)

        logger.info(f"Password reset code sent to {email_for_cognito}")

        return ForgotPasswordResponse(
            message=f"Password reset code sent to {code_delivery.get('Destination', 'your registered email')}. Please check your spam folder if you don't see it.",
            code_delivery_details=code_delivery,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm-forgot-password", response_model=MessageResponse)
async def confirm_forgot_password(
    request: ConfirmForgotPasswordRequest, db: Session = Depends(get_db)
):
    """
    Confirm forgot password with code and new password

    - **username**: Username or email address
    - **confirmation_code**: 6-digit verification code
    - **new_password**: New password (minimum 8 characters)
    """
    try:
        # Determine if username is an email or needs lookup
        email_for_cognito = request.username

        if "@" not in request.username:
            # Username provided, look up email from database
            user = db.query(User).filter(User.username == request.username).first()
            if user:
                email_for_cognito = user.email
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        cognito_service.confirm_forgot_password(
            username=email_for_cognito,
            confirmation_code=request.confirmation_code,
            new_password=request.new_password,
        )

        logger.info(f"Password reset completed for user {request.username}")

        return MessageResponse(
            message="Password reset successfully. You can now sign in with your new password.",
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confirm forgot password error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ConfirmForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password with code and new password (alias endpoint)

    This is an alias for /confirm-forgot-password to maintain compatibility with frontend.

    - **username**: Username or email address
    - **confirmation_code**: 6-digit verification code
    - **new_password**: New password (minimum 8 characters)
    """
    return await confirm_forgot_password(request, db)


@router.get("/user")
async def get_current_user(
    access_token: str = Depends(get_token_from_header), db: Session = Depends(get_db)
):
    """
    Get current user details from access token

    Requires Authorization header with Bearer token
    """
    try:
        # Get user info from Cognito
        cognito_user = cognito_service.get_user(access_token)

        # Get user from database
        user = (
            db.query(User)
            .filter(
                (User.cognito_user_id == cognito_user["user_sub"])
                | (User.firebase_id == cognito_user["user_sub"])
            )
            .first()
        )

        if not user:
            # Mock tokens impersonate users, so they must never work outside dev/test.
            if settings.ENVIRONMENT in ("development", "test", "testing") and (access_token.startswith("mock-") or access_token == "test-token"):
                return {
                    "id": 1,
                    "username": cognito_user.get("username", "farmer"),
                    "email": cognito_user.get("email", "farmer@cropsense.ai"),
                    "name": cognito_user.get("name", "Farmer"),
                    "user_type": "farmer",
                    "phone": cognito_user.get("phone_number", "+919876543210"),
                    "is_verified": 1,
                    "is_active": 1,
                    "cognito_user_id": cognito_user.get("user_sub"),
                    "firebase_id": cognito_user.get("user_sub"),
                    "email_verified": True,
                    "phone_verified": True,
                }
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database"
            )

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "user_type": user.user_type,
            "phone": user.phone,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "cognito_user_id": user.cognito_user_id,
            "firebase_id": user.firebase_id,
            "email_verified": cognito_user.get("email_verified", False),
            "phone_verified": cognito_user.get("phone_verified", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(access_token: str = Depends(get_token_from_header)):
    """
    Sign out user and invalidate tokens in Cognito
    """
    try:
        cognito_service.sign_out(access_token)
        return MessageResponse(message="Signed out successfully", success=True)
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Even if Cognito fails, we return success as the frontend will clear tokens
        return MessageResponse(message=f"Signed out with warning: {str(e)}", success=True)
