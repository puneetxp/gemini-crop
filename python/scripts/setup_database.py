#!/usr/bin/env python3
"""
Complete database setup script
Runs migrations, creates indexes, and optionally populates sample data
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, check_db_connection
from app.core.init_db import populate_sample_data, init_db
from app.core.vector_indexes import setup_all_vector_indexes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migrations():
    """Run Alembic migrations"""
    logger.info("Running database migrations...")
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Migrations completed successfully")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.warning("Alembic not found. Creating tables directly...")
        init_db()


def setup_database(with_sample_data: bool = False, skip_migrations: bool = False):
    """
    Complete database setup
    
    Args:
        with_sample_data: Whether to populate sample data
        skip_migrations: Skip running migrations (use direct table creation)
    """
    logger.info("=== Starting Database Setup ===")
    
    # Check database connection
    logger.info("Checking database connection...")
    if not check_db_connection():
        logger.error("Database connection failed. Please check your configuration.")
        sys.exit(1)
    
    logger.info("Database connection successful!")
    
    # Run migrations or create tables
    if not skip_migrations:
        run_migrations()
    else:
        logger.info("Skipping migrations, creating tables directly...")
        init_db()
    
    # Set up vector indexes
    logger.info("Setting up pgvector indexes...")
    db = SessionLocal()
    try:
        setup_all_vector_indexes(db)
    except Exception as e:
        logger.error(f"Error setting up vector indexes: {e}")
        raise
    finally:
        db.close()
    
    # Populate sample data if requested
    if with_sample_data:
        logger.info("Populating sample data...")
        db = SessionLocal()
        try:
            populate_sample_data(db)
        except Exception as e:
            logger.error(f"Error populating sample data: {e}")
            raise
        finally:
            db.close()
    
    logger.info("=== Database Setup Completed Successfully ===")
    logger.info("\nNext steps:")
    logger.info("1. Start the FastAPI server: uvicorn app.main:app --reload")
    logger.info("2. Access API docs at: http://localhost:8000/docs")
    logger.info("3. Check database with: psql -d cropsense_db")


def main():
    parser = argparse.ArgumentParser(description="Set up the CropSense AI database")
    parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Populate database with sample data for development/testing"
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip Alembic migrations and create tables directly"
    )
    
    args = parser.parse_args()
    
    try:
        setup_database(
            with_sample_data=args.with_sample_data,
            skip_migrations=args.skip_migrations
        )
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
