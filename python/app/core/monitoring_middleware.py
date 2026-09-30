"""
Monitoring Middleware for FastAPI
Task 20.3: Set up application monitoring

Automatically tracks API request metrics:
- Request count by endpoint and method
- Response times
- Error rates
- Status code distribution

Validates: Requirements (Non-Functional - Reliability)
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.monitoring import get_monitor

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track API request metrics in CloudWatch
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.monitor = get_monitor()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response from endpoint
        """
        # Skip monitoring for health check endpoints and OPTIONS requests (CORS preflight)
        if request.url.path in ["/health", "/ready", "/"] or request.method == "OPTIONS":
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Initialize response variables
        response = None
        status_code = 500  # Default to error if something goes wrong
        error_occurred = False
        error_type = None

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Check if error occurred
            if status_code >= 400:
                error_occurred = True
                error_type = f"HTTP{status_code}"

            return response

        except Exception as e:
            # Catch any unhandled exceptions
            error_occurred = True
            error_type = type(e).__name__
            logger.error(f"Unhandled exception in {request.method} {request.url.path}: {e}")
            raise

        finally:
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Track metrics in CloudWatch
            if self.monitor and self.monitor.enabled:
                try:
                    # Extract endpoint path (remove query parameters)
                    endpoint = request.url.path
                    method = request.method

                    # Get user ID if available
                    user_id = None
                    if hasattr(request.state, "user_id"):
                        user_id = request.state.user_id

                    # Track API request metrics
                    self.monitor.track_api_request(
                        endpoint=endpoint,
                        method=method,
                        status_code=status_code,
                        response_time_ms=response_time_ms,
                        user_id=user_id,
                    )

                    # Track error details if error occurred
                    if error_occurred and error_type:
                        self.monitor.track_api_error(
                            endpoint=endpoint,
                            method=method,
                            error_type=error_type,
                            error_message=f"Request failed with status {status_code}",
                        )

                    # Log slow requests (> 3 seconds)
                    if response_time_ms > 3000:
                        logger.warning(
                            f"Slow request detected: {method} {endpoint} "
                            f"took {response_time_ms:.2f}ms"
                        )

                except Exception as e:
                    # Don't let monitoring errors break the application
                    # Downgrade to warning to prevent local dev console spam
                    logger.warning(f"Failed to track metrics: {e}")


def get_monitoring_middleware() -> MonitoringMiddleware:
    """
    Get monitoring middleware instance

    Returns:
        MonitoringMiddleware instance
    """
    return MonitoringMiddleware
