#!/usr/bin/env python3
"""
Database migration script for CI/CD pipeline.
Runs Alembic migrations with proper error handling and rollback support.
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_revision(engine):
    """Get the current database revision."""
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_head_revision(alembic_cfg):
    """Get the head revision from migration scripts."""
    script = ScriptDirectory.from_config(alembic_cfg)
    return script.get_current_head()


def backup_database(database_url: str, backup_file: str):
    """Create a database backup before migration."""
    logger.info(f"Creating database backup to {backup_file}")
    
    # Extract database name from URL
    # Format: postgresql://user:pass@host:port/dbname
    db_name = database_url.split('/')[-1].split('?')[0]
    
    # Use pg_dump for backup
    os.system(f"pg_dump {database_url} > {backup_file}")
    logger.info("Database backup completed")


def run_migrations(dry_run: bool = False):
    """
    Run database migrations with safety checks.
    
    Args:
        dry_run: If True, only show what would be migrated without applying changes
    """
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Configure Alembic
    alembic_ini = Path(__file__).parent.parent / 'alembic.ini'
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option('sqlalchemy.url', database_url)
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        # Check database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
        # Get current and head revisions
        current_rev = get_current_revision(engine)
        head_rev = get_head_revision(alembic_cfg)
        
        logger.info(f"Current database revision: {current_rev}")
        logger.info(f"Target revision: {head_rev}")
        
        if current_rev == head_rev:
            logger.info("Database is already up to date")
            return True
        
        # Create backup in production
        if os.getenv('ENVIRONMENT') == 'production' and not dry_run:
            backup_file = f"/tmp/db_backup_{current_rev}.sql"
            backup_database(database_url, backup_file)
        
        if dry_run:
            logger.info("DRY RUN: Would apply the following migrations:")
            # Show pending migrations
            script = ScriptDirectory.from_config(alembic_cfg)
            for rev in script.iterate_revisions(head_rev, current_rev):
                logger.info(f"  - {rev.revision}: {rev.doc}")
            return True
        
        # Run migrations
        logger.info("Starting database migration...")
        command.upgrade(alembic_cfg, 'head')
        logger.info("Database migration completed successfully")
        
        # Verify migration
        new_rev = get_current_revision(engine)
        if new_rev == head_rev:
            logger.info(f"Migration verified: database is now at revision {new_rev}")
            return True
        else:
            logger.error(f"Migration verification failed: expected {head_rev}, got {new_rev}")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        logger.exception(e)
        
        # Attempt rollback in case of failure
        if not dry_run and current_rev:
            logger.info(f"Attempting to rollback to revision {current_rev}")
            try:
                command.downgrade(alembic_cfg, current_rev)
                logger.info("Rollback successful")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {str(rollback_error)}")
        
        return False
    
    finally:
        engine.dispose()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without applying changes'
    )
    
    args = parser.parse_args()
    
    success = run_migrations(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
