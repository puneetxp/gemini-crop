"""FastAPI entrypoint for CropSense AI - Rural Farming Platform."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import generated routers from routers.py (not __init__.py - using PEP 420)
from app.api.routers import all_routers

# Import v1 API routes
from app.api.v1 import (
    address,
    advance_booking,
    agents,
    ai_quota,
    analytics,
    annual_strategy,
    auth,
    community_dashboard,
    crop_milestones,
    crop_recommendations,
    crops,
    farms,
    fertilizer_recommendations,
    fertilizer_tracking,
    health,
    hybrid_ai,
    livestock,
    livestock_breeding,
    livestock_health,
    livestock_listings,
    livestock_marketplace,
    livestock_nutrition,
    livestock_transactions,
    market_data,
    market_intelligence,
    marketplace,
    model_training,
    notifications,
    pest_disease,
    plot_analysis,
    plot_publishing,
    predictive_analytics,
    sagemaker,
    severe_weather,
    slusi,
    soil,
    soil_health,
    soil_maps,
    soil_testing,
    supply_requests,
    transport,
    upload,
    users,
    vaccination_reminders,
    veterinary,
    vision_diagnosis,
    satellite,
    voice_agent,
    weather,
    weather_recommendations,
    yield_predictions,
)
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="AI-powered platform for rural farmers with predictive intelligence for crop management, direct marketplace access, and livestock optimization",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Security middlewares (order matters - add from innermost to outermost)
    from app.core.security_middleware import (
        CSRFProtectionMiddleware,
        RequestLoggingMiddleware,
        RequestValidationMiddleware,
        SecurityHeadersMiddleware,
    )

    # Add security headers to all responses
    app.add_middleware(SecurityHeadersMiddleware)

    # Add request validation (size limits, JSON complexity)
    app.add_middleware(RequestValidationMiddleware)

    # Add request logging for security monitoring
    if settings.LOG_LEVEL in ["DEBUG", "INFO"]:
        app.add_middleware(RequestLoggingMiddleware)

    # CSRF protection disabled for JWT-authenticated API endpoints (stateless authentication)
    # CSRF tokens are not generated or distributed to clients, and JWT Bearer tokens
    # already provide protection against CSRF attacks for stateless APIs.
    # If session-based authentication is added in the future, re-enable CSRF protection
    # with proper token generation (see TODO in security_middleware.py line 234)
    # app.add_middleware(CSRFProtectionMiddleware)

    # CORS middleware with strict origin validation
    allowed_origins = settings.get_allowed_origins_list()
    # In debug mode, we can be more permissive to help with local development across different IPs
    if settings.DEBUG and "*" not in allowed_origins:
        allowed_origins.append("*")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],  # Allow all headers for maximum compatibility
        max_age=3600,
    )

    # Initialize CloudWatch monitoring middleware
    monitoring_enabled = getattr(settings, "MONITORING_ENABLED", True)
    if monitoring_enabled:
        try:
            from app.core.monitoring import init_monitor
            from app.core.monitoring_middleware import MonitoringMiddleware

            # Initialize monitor synchronously
            monitor = init_monitor(
                namespace="RuralFarmingPlatform",
                region=getattr(settings, "AWS_REGION", "ap-south-1"),
                enabled=True,
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            )

            # Add monitoring middleware
            app.add_middleware(MonitoringMiddleware)

            logger.info("CloudWatch monitoring initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch monitoring: {e}. Monitoring disabled.")
    else:
        logger.info("CloudWatch monitoring disabled by configuration")

    # Initialize rate limiting middleware
    if settings.RATE_LIMIT_ENABLED:
        try:
            from app.core.rate_limiter import init_rate_limiter

            # Initialize rate limiter metadata
            rate_limiter = init_rate_limiter(
                redis_url=settings.REDIS_URL,
                default_limit=settings.RATE_LIMIT_PER_MINUTE,
                window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
                enabled=True,
            )

            # Get and add rate limiting middleware
            from starlette.middleware.base import BaseHTTPMiddleware

            middleware_func = rate_limiter.get_middleware(
                limit=settings.RATE_LIMIT_PER_MINUTE,
                window=settings.RATE_LIMIT_WINDOW_SECONDS,
                public_limit=settings.RATE_LIMIT_PUBLIC_PER_MINUTE,
            )
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware_func)
            logger.info("Rate limiter middleware added (will connect to Redis on startup)")
        except Exception as e:
            logger.warning(f"Failed to add rate limit middleware: {e}. Rate limiting disabled.")

    # Include generated routers (CRUD operations from schema-driven generation)
    logger.info("Loading generated CRUD routers...")
    # Guard by namespace here, not in the generated files, so regeneration can't drop the auth:
    # /isuper -> admin only, /islogin -> any signed-in user, /ipublic -> open.
    from fastapi import Depends

    from app.core.auth import get_current_active_user, get_current_admin, require_role

    namespace_guards = {
        "/isuper": [Depends(get_current_admin)],
        "/islogin": [Depends(get_current_active_user)],
        # Custom role controllers (crud.roles in the model JSON): only users with that role
        "/service_provider": [Depends(require_role(["service_provider", "admin"]))],
    }
    for router in all_routers:
        guard = next(
            (deps for ns, deps in namespace_guards.items() if router.prefix.startswith(ns)), []
        )
        app.include_router(router, prefix=settings.API_V1_STR, dependencies=guard)

    # Include v1 API routers (custom business logic)
    # IMPORTANT: Register specific routes BEFORE catch-all routes to avoid conflicts
    logger.info("Loading v1 API routers...")
    app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
    app.include_router(farms.router, prefix=settings.API_V1_STR, tags=["Farms"])
    # Users router has /{user_id} catch-all route, so register it AFTER specific routes
    app.include_router(users.router, prefix=settings.API_V1_STR, tags=["Users"])
    app.include_router(crops.router, prefix=settings.API_V1_STR, tags=["Crops"])
    app.include_router(
        crop_recommendations.router, prefix=settings.API_V1_STR, tags=["Crop Recommendations"]
    )
    app.include_router(crop_milestones.router, prefix=settings.API_V1_STR, tags=["Crop Milestones"])
    app.include_router(annual_strategy.router, prefix=settings.API_V1_STR, tags=["Annual Strategy"])
    app.include_router(market_data.router, prefix=settings.API_V1_STR, tags=["Market Data"])
    app.include_router(marketplace.router, prefix=settings.API_V1_STR, tags=["Marketplace"])
    app.include_router(
        advance_booking.router,
        prefix=settings.API_V1_STR + "/marketplace",
        tags=["Advance Booking"],
    )
    app.include_router(upload.router, prefix=settings.API_V1_STR + "/upload", tags=["File Upload"])
    app.include_router(weather.router, prefix=settings.API_V1_STR, tags=["Weather"])
    app.include_router(severe_weather.router, prefix=settings.API_V1_STR, tags=["Severe Weather"])
    app.include_router(
        weather_recommendations.router, prefix=settings.API_V1_STR, tags=["Weather Recommendations"]
    )
    app.include_router(notifications.router, prefix=settings.API_V1_STR, tags=["Notifications"])
    app.include_router(
        yield_predictions.router, prefix=settings.API_V1_STR, tags=["Yield Predictions"]
    )
    app.include_router(soil.router, prefix=settings.API_V1_STR, tags=["Soil Management"])
    app.include_router(soil_testing.router, prefix=settings.API_V1_STR, tags=["Soil Testing"])
    app.include_router(soil_maps.router, prefix=settings.API_V1_STR, tags=["Soil Maps"])
    app.include_router(soil_health.router, prefix=settings.API_V1_STR, tags=["Soil Health"])
    app.include_router(
        fertilizer_recommendations.router,
        prefix=settings.API_V1_STR,
        tags=["Fertilizer Recommendations"],
    )
    app.include_router(
        fertilizer_tracking.router, prefix=settings.API_V1_STR, tags=["Fertilizer Tracking"]
    )
    app.include_router(pest_disease.router, prefix=settings.API_V1_STR, tags=["Pest & Disease"])
    app.include_router(livestock.router, prefix=settings.API_V1_STR, tags=["Livestock Management"])
    app.include_router(
        livestock_health.router, prefix=settings.API_V1_STR, tags=["Livestock Health"]
    )
    app.include_router(
        livestock_nutrition.router, prefix=settings.API_V1_STR, tags=["Livestock Nutrition"]
    )
    app.include_router(
        livestock_breeding.router, prefix=settings.API_V1_STR, tags=["Livestock Breeding"]
    )
    app.include_router(
        livestock_transactions.router, prefix=settings.API_V1_STR, tags=["Livestock Transactions"]
    )
    # These were built but never mounted (see FEATURES.md, "built but not wired up").
    app.include_router(
        livestock_listings.router, prefix=settings.API_V1_STR, tags=["Livestock Listings"]
    )
    app.include_router(
        livestock_marketplace.router, prefix=settings.API_V1_STR, tags=["Livestock Marketplace"]
    )
    app.include_router(supply_requests.router, prefix=settings.API_V1_STR, tags=["Supply Requests"])
    app.include_router(
        vaccination_reminders.router, prefix=settings.API_V1_STR, tags=["Vaccination Reminders"]
    )
    app.include_router(veterinary.router, prefix=settings.API_V1_STR, tags=["Veterinary Services"])
    app.include_router(
        sagemaker.router, prefix=settings.API_V1_STR, tags=["SageMaker Infrastructure"]
    )
    app.include_router(model_training.router, prefix=settings.API_V1_STR, tags=["Model Training"])
    app.include_router(hybrid_ai.router, prefix=settings.API_V1_STR, tags=["Hybrid AI"])
    app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])
    app.include_router(
        predictive_analytics.router, prefix=settings.API_V1_STR, tags=["Predictive Analytics"]
    )
    app.include_router(plot_analysis.router, prefix=settings.API_V1_STR, tags=["Plot Analysis"])
    app.include_router(plot_publishing.router, prefix=settings.API_V1_STR, tags=["Plot Publishing"])
    app.include_router(ai_quota.router, prefix=settings.API_V1_STR, tags=["AI Quota"])
    app.include_router(address.router, prefix=settings.API_V1_STR, tags=["Address Management"])
    app.include_router(
        market_intelligence.router, prefix=settings.API_V1_STR, tags=["Market Intelligence"]
    )
    app.include_router(transport.router, prefix=settings.API_V1_STR, tags=["Transport"])
    app.include_router(slusi.router, prefix=settings.API_V1_STR, tags=["SLUSI Soil Data"])
    app.include_router(agents.router, prefix=settings.API_V1_STR, tags=["Agents"])
    app.include_router(vision_diagnosis.router, prefix=settings.API_V1_STR, tags=["Vision AI"])
    app.include_router(satellite.router, prefix=settings.API_V1_STR, tags=["Satellite"])
    app.include_router(voice_agent.router, prefix=settings.API_V1_STR, tags=["Voice AI"])
    app.include_router(
        community_dashboard.router, prefix=settings.API_V1_STR, tags=["Community Intelligence"]
    )
    app.include_router(health.router, tags=["Health"])  # Health checks at root level

    logger.info(f"{settings.APP_NAME} v{settings.VERSION} initialized successfully")

    return app


app = create_app()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


async def _start_background_jobs():
    """Schedulers and one-off seeding that reach external services (skipped in E2E mode)."""
    # Initialize quota reset scheduler
    try:
        from app.jobs.quota_reset_job import start_quota_reset_scheduler

        scheduler = start_quota_reset_scheduler()
        # Store scheduler in app state for shutdown
        app.state.quota_scheduler = scheduler
        logger.info("Quota reset scheduler started (runs at midnight IST daily)")
    except Exception as e:
        logger.error(f"Failed to start quota reset scheduler: {e}")
        app.state.quota_scheduler = None

    # Initialize SLUSI ingestion scheduler
    try:
        from app.jobs.slusi_ingestion_job import start_slusi_scheduler

        slusi_scheduler = start_slusi_scheduler()
        app.state.slusi_scheduler = slusi_scheduler
        logger.info(
            f"SLUSI ingestion scheduler started (every {settings.SLUSI_INGEST_INTERVAL_DAYS} days)"
        )
    except Exception as e:
        logger.error(f"Failed to start SLUSI ingestion scheduler: {e}")
        app.state.slusi_scheduler = None

    # Seed SHC state/district codes if table is empty
    try:
        from sqlalchemy import text

        from app.core.database import get_db_context
        from app.services.shc_code_mapper import SHCCodeMapper

        with get_db_context() as db:
            count = db.execute(text("SELECT COUNT(*) FROM shc_state_district_codes")).scalar() or 0
            if count == 0:
                logger.info("shc_state_district_codes is empty — seeding from GraphQL API")
                mapper = SHCCodeMapper()
                seeded = await mapper.seed_database(db)
                logger.info(f"Seeded {seeded} state/district code rows")
            else:
                logger.info(f"shc_state_district_codes already has {count} rows — skipping seed")
    except Exception as e:
        logger.warning(f"Failed to seed SHC state/district codes: {e}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize cache manager
    if settings.CACHE_ENABLED:
        try:
            from app.core.cache import init_cache_manager

            cache_manager = init_cache_manager(
                redis_url=settings.REDIS_URL, default_ttl=settings.CACHE_TTL_SECONDS, enabled=True
            )
            logger.info(
                f"Cache manager initialized (Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT})"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize cache manager: {e}. Caching disabled.")
    else:
        logger.info("Caching disabled by configuration")

    # Connect rate limiter to Redis
    if settings.RATE_LIMIT_ENABLED:
        try:
            from app.core.rate_limiter import get_rate_limiter

            rate_limiter = get_rate_limiter()
            if rate_limiter:
                await rate_limiter.init()
                logger.info(
                    f"Rate limiter connected (Authenticated: {settings.RATE_LIMIT_PER_MINUTE}/min, Public: {settings.RATE_LIMIT_PUBLIC_PER_MINUTE}/min)"
                )
        except Exception as e:
            logger.warning(f"Failed to connect rate limiter to Redis on startup: {e}")
    else:
        logger.info("Rate limiting disabled by configuration")

    if settings.E2E_ACTIVE:
        logger.warning("E2E mode: background schedulers and SHC code seeding are off")
        app.state.quota_scheduler = None
        app.state.slusi_scheduler = None
    else:
        await _start_background_jobs()

    # Check database connection
    from app.core.database import check_db_connection

    if check_db_connection():
        logger.info("Database connection successful")
    else:
        logger.warning("Database connection failed - check configuration")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Stop quota reset scheduler
    if hasattr(app.state, "quota_scheduler") and app.state.quota_scheduler:
        try:
            from app.jobs.quota_reset_job import stop_quota_reset_scheduler

            stop_quota_reset_scheduler(app.state.quota_scheduler)
            logger.info("Quota reset scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping quota reset scheduler: {e}")

    # Stop SLUSI ingestion scheduler
    if hasattr(app.state, "slusi_scheduler") and app.state.slusi_scheduler:
        try:
            from app.jobs.slusi_ingestion_job import stop_slusi_scheduler

            stop_slusi_scheduler(app.state.slusi_scheduler)
            logger.info("SLUSI ingestion scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping SLUSI ingestion scheduler: {e}")

    # Close rate limiter connection
    if settings.RATE_LIMIT_ENABLED:
        try:
            from app.core.rate_limiter import get_rate_limiter

            rate_limiter = get_rate_limiter()
            if rate_limiter:
                await rate_limiter.close()
                logger.info("Rate limiter connection closed")
        except Exception as e:
            logger.warning(f"Error closing rate limiter: {e}")

    # Close database connections
    from app.core.database import close_db_connections

    close_db_connections()
    logger.info("Database connections closed")


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
