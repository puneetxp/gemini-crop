"""
Security middleware for request validation and security headers
"""

import logging
import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.validation import RequestSizeValidator

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        # Note: For /docs endpoint (Swagger UI), we need to allow CDN resources
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",  # Allow Swagger UI scripts
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # Allow Swagger UI styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            # App Engine backend + Firebase Hosting frontend + AWS services
            "connect-src 'self' https://*.appspot.com https://*.web.app https://*.firebaseapp.com https://cognito-idp.ap-south-1.amazonaws.com https://bedrock-runtime.ap-south-1.amazonaws.com https://cognito-idp.us-east-1.amazonaws.com https://bedrock-runtime.us-east-1.amazonaws.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate request size and content"""

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request before processing"""

        # Skip validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request too large. Maximum size: {self.MAX_REQUEST_SIZE / (1024 * 1024)}MB"
                        },
                    )
            except ValueError:
                pass

        # Validate JSON body size and complexity for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # Get body
                    body = await request.body()

                    # Check body size
                    if len(body) > self.MAX_REQUEST_SIZE:
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={
                                "detail": f"Request body too large. Maximum size: {self.MAX_REQUEST_SIZE / (1024 * 1024)}MB"
                            },
                        )

                    # Parse and validate JSON complexity
                    if body:
                        import json

                        try:
                            data = json.loads(body)
                            RequestSizeValidator.validate_json_size(data)
                        except json.JSONDecodeError:
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Invalid JSON format"},
                            )
                        except HTTPException as e:
                            return JSONResponse(
                                status_code=e.status_code, content={"detail": e.detail}
                            )

                    # Reconstruct request with body
                    async def receive():
                        return {"type": "http.request", "body": body}

                    request._receive = receive

                except Exception as e:
                    logger.error(f"Error validating request: {e}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid request"},
                    )

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details"""

        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} "
                f"for {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )
            raise


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing operations"""

    SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]
    CSRF_HEADER = "X-CSRF-Token"

    def __init__(self, app: ASGIApp, exempt_paths: list[str] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/signin",
            "/auth/signup",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CSRF token for state-changing requests"""

        # Skip CSRF check for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # For now, we'll skip CSRF validation as it requires session management
        # In production, implement proper CSRF token validation with session storage
        # TODO: Implement CSRF token generation and validation with Redis session storage

        return await call_next(request)
