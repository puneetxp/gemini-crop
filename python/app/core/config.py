"""
Configuration module for CropSense AI backend service.
Handles environment variables, GCP Secret Manager integration, database settings,
Firebase authentication keys, AI models, and service limits.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus


# Simple .env loader without third-party dependencies
def _load_env_file():
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path("python/.env")
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass


_load_env_file()


class Settings:
    """Centralized application settings for CropSense AI."""

    # Application Identity
    APP_NAME: str = os.getenv("APP_NAME", "CropSense AI")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "CropSense AI")
    VERSION: str = os.getenv("VERSION", "1.0.0")

    # Environment
    ENV: str = os.getenv("APP_ENV", os.getenv("ENV", os.getenv("ENVIRONMENT", "development")))
    ENVIRONMENT: str = ENV
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # E2E test mode
    E2E_MODE: bool = os.getenv("E2E_MODE", "false").lower() in ("true", "1", "yes")
    E2E_PASSWORD: str = os.getenv("E2E_PASSWORD", "E2e-Test-Pass1!")

    @property
    def E2E_ACTIVE(self) -> bool:
        if os.getenv("E2E_ACTIVE", "").lower() in ("true", "1", "yes"):
            return True
        return (
            self.E2E_MODE
            and self.ENVIRONMENT == "test"
            and self.DB_NAME.endswith("_e2e")
            and not os.getenv("K_SERVICE")
        )

    # API Configuration
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "test-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # CORS & Allowed Hosts
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:4200,http://localhost:4321,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:4321,http://127.0.0.1:5173",
    )
    ALLOWED_HOSTS: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,192.168.1.5")
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:4321",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4321",
        "http://127.0.0.1:5173",
    ]

    # Security Settings
    MAX_REQUEST_SIZE_MB: int = int(os.getenv("MAX_REQUEST_SIZE_MB", "10"))
    MAX_JSON_FIELDS: int = int(os.getenv("MAX_JSON_FIELDS", "1000"))
    MAX_STRING_LENGTH: int = int(os.getenv("MAX_STRING_LENGTH", "10000"))
    MAX_ARRAY_LENGTH: int = int(os.getenv("MAX_ARRAY_LENGTH", "1000"))
    ENABLE_CSRF_PROTECTION: bool = os.getenv("ENABLE_CSRF_PROTECTION", "false").lower() in ("true", "1", "yes")
    ENABLE_REQUEST_LOGGING: bool = os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() in ("true", "1", "yes")

    # Database Configuration (PostgreSQL / psycopg3 / SQLAlchemy)
    DB_HOST: str = os.getenv("DB_HOST", os.getenv("POSTGRES_SERVER", os.getenv("POSTGRES_HOST", "localhost")))
    POSTGRES_SERVER: str = DB_HOST
    DB_PORT: int = int(os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432")))
    POSTGRES_PORT: int = DB_PORT
    DB_NAME: str = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "cropsense_db"))
    POSTGRES_DB: str = DB_NAME
    DB_USER: str = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
    POSTGRES_USER: str = DB_USER
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "password"))
    POSTGRES_PASSWORD: str = DB_PASSWORD
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "2"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "2"))
    DB_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "30"))

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        if self.DB_HOST.startswith("/"):
            return f"postgresql+psycopg://{user}:{password}@/{self.DB_NAME}?host={self.DB_HOST}"
        return f"postgresql+psycopg://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = os.getenv("ASYNC_DATABASE_URL")
        if url:
            return url
        return self.DATABASE_URL

    # Redis Cache & Rate Limiting
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def REDIS_URL(self) -> str:
        custom_url = os.getenv("REDIS_URL")
        if custom_url:
            return custom_url
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Google Cloud & Firebase Configuration
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "cropsense-ai-prod")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    GOOGLE_CLOUD_REGION: str = os.getenv("GOOGLE_CLOUD_REGION", "asia-south1")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "cropsense-ai-prod")
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH", None)

    # Gemini AI Models & Settings (3.8 Flash & 3.5 Flash Lite)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GEMINI_ASSIST_MODEL: str = os.getenv("GEMINI_ASSIST_MODEL", "gemini-3.5-flash-lite")
    GEMINI_FALLBACK_MODELS: List[str] = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

    # Cloud SQL & Storage
    CLOUD_SQL_INSTANCE: Optional[str] = os.getenv("CLOUD_SQL_INSTANCE", None)
    GOOGLE_CLOUD_SQL_INSTANCE: Optional[str] = os.getenv("GOOGLE_CLOUD_SQL_INSTANCE", None)
    CLOUD_SQL_DB: str = os.getenv("CLOUD_SQL_DB", "cropsense_db")
    GCS_BUCKET: str = os.getenv("GCS_BUCKET", "cropsense-assets")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "cropsense_analytics")
    FIRESTORE_COLLECTION_PREFIX: str = os.getenv("FIRESTORE_COLLECTION_PREFIX", "cropsense")

    # External APIs
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "test-api-key")
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY", None)
    DATAGOV_API_KEY: Optional[str] = os.getenv("DATAGOV_API_KEY", None)
    DATAGOV_MOISTURE_API_KEY: Optional[str] = os.getenv("DATAGOV_MOISTURE_API_KEY", None)

    # SMS & Notifications
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN", None)
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER", None)

    # Web Push (VAPID) Configuration
    VAPID_PUBLIC_KEY: Optional[str] = os.getenv("VAPID_PUBLIC_KEY", None)
    VAPID_PRIVATE_KEY: Optional[str] = os.getenv("VAPID_PRIVATE_KEY", None)
    VAPID_SUBJECT: str = os.getenv("VAPID_SUBJECT", "mailto:admin@cropsense.ai")

    # Email Configuration
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")

    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))
    ALLOWED_IMAGE_EXTENSIONS: str = os.getenv("ALLOWED_IMAGE_EXTENSIONS", ".jpg,.jpeg,.png,.gif,.webp")

    # ML & SageMaker Configuration
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "models/")
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    SAGEMAKER_MODEL_BUCKET: str = os.getenv("SAGEMAKER_MODEL_BUCKET", "cropsense-sagemaker-models")
    SAGEMAKER_EXECUTION_ROLE_ARN: Optional[str] = os.getenv("SAGEMAKER_EXECUTION_ROLE_ARN", None)
    SAGEMAKER_ENDPOINT_PREFIX: str = os.getenv("SAGEMAKER_ENDPOINT_PREFIX", "cropsense")
    SAGEMAKER_ENABLED: bool = os.getenv("SAGEMAKER_ENABLED", "false").lower() in ("true", "1", "yes")
    SAGEMAKER_YIELD_ENDPOINT: str = os.getenv("SAGEMAKER_YIELD_ENDPOINT", "cropsense-yield-prediction")
    SAGEMAKER_HARVEST_ENDPOINT: str = os.getenv("SAGEMAKER_HARVEST_ENDPOINT", "cropsense-harvest-prediction")
    SAGEMAKER_QUALITY_ENDPOINT: str = os.getenv("SAGEMAKER_QUALITY_ENDPOINT", "cropsense-quality-prediction")

    # Caching
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    WEATHER_CACHE_TTL: int = int(os.getenv("WEATHER_CACHE_TTL", "21600"))
    FARM_CACHE_TTL: int = int(os.getenv("FARM_CACHE_TTL", "3600"))
    MARKETPLACE_CACHE_TTL: int = int(os.getenv("MARKETPLACE_CACHE_TTL", "60"))
    STRATEGY_CACHE_TTL: int = int(os.getenv("STRATEGY_CACHE_TTL", "7200"))
    MARKET_DATA_CACHE_TTL: int = int(os.getenv("MARKET_DATA_CACHE_TTL", "86400"))

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PUBLIC_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "20"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_PUBLIC: int = int(os.getenv("RATE_LIMIT_PUBLIC", "20"))
    RATE_LIMIT_AUTH: int = int(os.getenv("RATE_LIMIT_AUTH", "100"))

    # Logging & Monitoring
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() in ("true", "1", "yes")
    MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "false").lower() in ("true", "1", "yes")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    DYNAMODB_TABLE_PREFIX: str = os.getenv("DYNAMODB_TABLE_PREFIX", "cropsense")

    # Soil Health Card & SLUSI
    SHC_WMS_PATH: str = os.getenv("SHC_WMS_PATH", "")
    SHC_CYCLE: str = os.getenv("SHC_CYCLE", "2025-26")
    SHC_WMS_BASE: str = os.getenv("SHC_WMS_BASE", "https://soilhealth4.dac.gov.in")
    SLUSI_INGEST_INTERVAL_DAYS: int = int(os.getenv("SLUSI_INGEST_INTERVAL_DAYS", "7"))

    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = os.getenv("CELERY_BROKER_URL", None)
    CELERY_RESULT_BACKEND: Optional[str] = os.getenv("CELERY_RESULT_BACKEND", None)

    def get_allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS

    def get_allowed_hosts_list(self) -> List[str]:
        """Get ALLOWED_HOSTS as a list"""
        if isinstance(self.ALLOWED_HOSTS, str):
            return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
        return self.ALLOWED_HOSTS

    def get_allowed_extensions_list(self) -> List[str]:
        """Get ALLOWED_IMAGE_EXTENSIONS as a list"""
        if isinstance(self.ALLOWED_IMAGE_EXTENSIONS, str):
            return [ext.strip() for ext in self.ALLOWED_IMAGE_EXTENSIONS.split(",") if ext.strip()]
        return self.ALLOWED_IMAGE_EXTENSIONS


settings = Settings()


class DynamoDBTables:
    """DynamoDB table names with prefix"""

    @staticmethod
    def get_table_name(base_name: str) -> str:
        return f"{settings.DYNAMODB_TABLE_PREFIX}-{base_name}"

    CROP_PREDICTIONS = property(lambda self: self.get_table_name("crop-predictions"))
    USER_ANALYTICS = property(lambda self: self.get_table_name("user-analytics"))
    WEATHER_CACHE = property(lambda self: self.get_table_name("weather-cache"))
    NOTIFICATIONS = property(lambda self: self.get_table_name("notifications"))
    RECOMMENDATIONS = property(lambda self: self.get_table_name("recommendations"))


dynamodb_tables = DynamoDBTables()


def validate_settings():
    """Validate critical settings - only in production"""
    if settings.E2E_MODE and not settings.E2E_ACTIVE:
        raise ValueError(
            "E2E_MODE requires ENVIRONMENT=test and a POSTGRES_DB ending in _e2e, and is refused on Cloud Run"
        )

    if settings.ENVIRONMENT in ["test", "testing", "development"]:
        return

    errors = []
    if settings.SECRET_KEY == "test-secret-key-change-in-production":
        errors.append("SECRET_KEY must be changed in production")
    if settings.OPENWEATHER_API_KEY == "test-api-key":
        errors.append("OPENWEATHER_API_KEY must be configured in production")
    if errors:
        raise ValueError(f"Production configuration errors: {', '.join(errors)}")


if os.getenv("SKIP_VALIDATION") != "true":
    try:
        validate_settings()
    except Exception:
        if settings.ENVIRONMENT not in ["test", "testing", "development"]:
            raise


def get_system_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Resolves settings dynamically from the system_settings database table,
    falling back to environment variables and configuration defaults.
    """
    try:
        from app.orm.system_setting import SystemSetting

        setting = SystemSetting.find(key, "key")
        if setting and setting.items:
            if setting.items.get("enable", 1) == 1:
                return setting.items.get("value")
    except Exception:
        pass

    val = os.getenv(key)
    if val is not None:
        return val

    if hasattr(settings, key):
        return getattr(settings, key)

    return default
