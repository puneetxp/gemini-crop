"""
Database configuration and session management
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engines, using Cloud SQL Connector in cloud environment and standard connections locally
if getattr(settings, "GOOGLE_CLOUD_SQL_INSTANCE", None):
    logger.info("Initializing database using Cloud SQL Python Connector (PostgreSQL)...")
    from google.cloud.sql.connector import Connector, IPTypes

    # Initialize connector
    connector = Connector()

    def getconn():
        return connector.connect(
            settings.GOOGLE_CLOUD_SQL_INSTANCE,
            "psycopg",
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            db=settings.POSTGRES_DB,
            ip_type=IPTypes.PUBLIC,
        )

    async def getasyncconn():
        return await connector.connect_async(
            settings.GOOGLE_CLOUD_SQL_INSTANCE,
            "psycopg",
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            db=settings.POSTGRES_DB,
            ip_type=IPTypes.PUBLIC,
        )

    engine = create_engine(
        "postgresql+psycopg://",
        creator=getconn,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )

    async_engine = create_async_engine(
        "postgresql+psycopg://",
        async_creator=getasyncconn,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )
else:
    logger.info("Initializing database using local connection strings (PostgreSQL)...")
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,  # Maximum number of connections to keep open
        max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
        pool_pre_ping=True,  # Test connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=settings.DEBUG,
    )

    # Create async engine for async operations
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )

# Create SessionLocal class for synchronous operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)

# Create AsyncSessionLocal for async operations
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create Base class for models
Base = declarative_base()


# Event listeners for connection management
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new database connections"""
    logger.debug("Database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Event listener for closed database connections"""
    logger.debug("Database connection closed")


# Dependency to get DB session (synchronous)
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database sessions for FastAPI endpoints

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


# Async dependency to get DB session
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency function that yields database sessions for async FastAPI endpoints

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()


# Context manager for manual session management
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for manual database session management

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database context error: {e}")
        raise
    finally:
        db.close()


# Async context manager for manual session management
@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for manual database session management

    Usage:
        async with get_async_db_context() as db:
            result = await db.execute(select(User))
            user = result.scalar_one_or_none()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database context error: {e}")
            raise
        finally:
            await session.close()


# Database initialization and health check
def init_db() -> None:
    """
    Initialize database - create all tables
    Note: In production, use Alembic migrations instead
    """
    try:
        # NOTE (2026-09-26): don't use this to create tables. The schema is owned by database/Model/*.json
        # + `php setup.php` (see skills/SKILL.md); SQLAlchemy here is only a connection pool / the users model.
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def check_async_db_connection() -> bool:
    """
    Check if async database connection is working

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Async database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Async database connection check failed: {e}")
        return False


# Cleanup function
def close_db_connections() -> None:
    """
    Close all database connections
    Call this on application shutdown
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def close_async_db_connections() -> None:
    """
    Close all async database connections
    Call this on application shutdown
    """
    try:
        await async_engine.dispose()
        logger.info("Async database connections closed")
    except Exception as e:
        logger.error(f"Error closing async database connections: {e}")
