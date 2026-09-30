"""
Health Check Endpoints for Load Balancer
Task 20.3: Set up application monitoring

Provides:
- /health - Basic health check (fast, for load balancer)
- /ready - Readiness check (checks all dependencies)
- /health/detailed - Comprehensive health status

Validates: Requirements (Non-Functional - Reliability)
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.monitoring import get_monitor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    tags=["Health"],
    summary="Basic health check",
    description="Fast health check for load balancer. Returns 200 if application is running.",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancer

    This endpoint is designed to be fast and lightweight.
    It only checks if the application is running.

    Returns:
        200 OK if application is healthy
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness check",
    description="Liveness check for load balancer. Returns 200 if application is running.",
    status_code=status.HTTP_200_OK,
)
async def liveness_check() -> Dict[str, Any]:
    """Alias for basic health check"""
    return await health_check()


@router.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness check",
    description="Comprehensive readiness check. Verifies all dependencies are available.",
    status_code=status.HTTP_200_OK,
)
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint for load balancer

    This endpoint checks if the application is ready to serve traffic.
    It verifies connectivity to all critical dependencies:
    - Database (PostgreSQL)
    - Cache (Redis)
    - AI Service (Bedrock)

    Returns:
        200 OK if all dependencies are healthy
        503 Service Unavailable if any dependency is unhealthy
    """
    monitor = get_monitor()

    if not monitor:
        # If monitoring is not initialized, do basic checks
        from app.core.database import check_db_connection

        db_healthy = check_db_connection()

        if not db_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "service": settings.APP_NAME,
                    "version": settings.VERSION,
                    "reason": "Database connection failed",
                },
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "service": settings.APP_NAME, "version": settings.VERSION},
        )

    # Get comprehensive health status
    health_status = await monitor.get_comprehensive_health()

    # Determine if application is ready
    is_ready = health_status["status"] in ["healthy", "degraded"]

    # Return appropriate status code
    if is_ready:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "service": settings.APP_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "health": health_status,
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": settings.APP_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "health": health_status,
            },
        )


@router.get(
    "/health/detailed",
    tags=["Health"],
    summary="Detailed health status",
    description="Comprehensive health status of all services and dependencies.",
    status_code=status.HTTP_200_OK,
)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint

    Provides comprehensive health status including:
    - Application status
    - Database connectivity and performance
    - Redis cache status and performance
    - Bedrock API connectivity
    - Response times for each service

    This endpoint is more expensive than /health and /ready,
    so it should not be used for load balancer health checks.
    Use it for monitoring dashboards and debugging.

    Returns:
        Detailed health status of all services
    """
    monitor = get_monitor()

    if not monitor:
        return {
            "status": "monitoring_disabled",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "message": "CloudWatch monitoring is not enabled",
        }

    # Get comprehensive health status
    health_status = await monitor.get_comprehensive_health()

    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "health": health_status,
        "configuration": {
            "cache_enabled": settings.CACHE_ENABLED,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
            "monitoring_enabled": monitor.enabled,
        },
    }


@router.get(
    "/health/database",
    tags=["Health"],
    summary="Database health check",
    description="Check database connectivity and performance.",
    status_code=status.HTTP_200_OK,
)
async def database_health_check() -> Dict[str, Any]:
    """
    Database-specific health check

    Returns:
        Database health status
    """
    monitor = get_monitor()

    if not monitor:
        from app.core.database import check_db_connection

        is_healthy = check_db_connection()

        return {"status": "healthy" if is_healthy else "unhealthy", "service": "database"}

    db_health = await monitor.check_database_health()
    return {"service": "database", "health": db_health}


@router.get(
    "/health/redis",
    tags=["Health"],
    summary="Redis health check",
    description="Check Redis cache connectivity and performance.",
    status_code=status.HTTP_200_OK,
)
async def redis_health_check() -> Dict[str, Any]:
    """
    Redis-specific health check

    Returns:
        Redis health status
    """
    monitor = get_monitor()

    if not monitor:
        return {"status": "monitoring_disabled", "service": "redis"}

    redis_health = await monitor.check_redis_health()
    return {"service": "redis", "health": redis_health}


@router.get(
    "/health/bedrock",
    tags=["Health"],
    summary="Bedrock health check",
    description="Check Bedrock API connectivity.",
    status_code=status.HTTP_200_OK,
)
async def bedrock_health_check() -> Dict[str, Any]:
    """
    Bedrock-specific health check

    Returns:
        Bedrock health status
    """
    monitor = get_monitor()

    if not monitor:
        return {"status": "monitoring_disabled", "service": "bedrock"}

    bedrock_health = await monitor.check_bedrock_health()
    return {"service": "bedrock", "health": bedrock_health}
