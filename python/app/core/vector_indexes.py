"""
pgvector index setup and management for similarity search
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_vector_extension(db: Session) -> None:
    """
    Create pgvector extension if it doesn't exist
    """
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
        logger.info("pgvector extension created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating pgvector extension: {e}")
        db.rollback()
        raise


def create_ivfflat_index(
    db: Session, table_name: str, column_name: str, lists: int = 100, index_name: str = None
) -> None:
    """
    Create IVFFlat index for approximate nearest neighbor search

    Args:
        db: Database session
        table_name: Name of the table
        column_name: Name of the vector column
        lists: Number of lists for IVFFlat (default: 100)
        index_name: Custom index name (optional)

    IVFFlat is good for:
    - Large datasets (>10k vectors)
    - Faster search with slight accuracy tradeoff
    - Recommended lists: sqrt(total_rows)
    """
    if index_name is None:
        index_name = f"idx_{table_name}_{column_name}_ivfflat"

    try:
        # Create IVFFlat index
        query = text(f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name}
            USING ivfflat ({column_name} vector_cosine_ops)
            WITH (lists = {lists})
        """)
        db.execute(query)
        db.commit()
        logger.info(
            f"IVFFlat index '{index_name}' created successfully on {table_name}.{column_name}"
        )
    except Exception as e:
        logger.error(f"Error creating IVFFlat index: {e}")
        db.rollback()
        raise


def create_hnsw_index(
    db: Session,
    table_name: str,
    column_name: str,
    m: int = 16,
    ef_construction: int = 64,
    index_name: str = None,
) -> None:
    """
    Create HNSW index for approximate nearest neighbor search

    Args:
        db: Database session
        table_name: Name of the table
        column_name: Name of the vector column
        m: Maximum number of connections per layer (default: 16)
        ef_construction: Size of dynamic candidate list (default: 64)
        index_name: Custom index name (optional)

    HNSW is good for:
    - High accuracy requirements
    - Faster build time than IVFFlat
    - Better recall at the cost of more memory
    """
    if index_name is None:
        index_name = f"idx_{table_name}_{column_name}_hnsw"

    try:
        # Create HNSW index
        query = text(f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name}
            USING hnsw ({column_name} vector_cosine_ops)
            WITH (m = {m}, ef_construction = {ef_construction})
        """)
        db.execute(query)
        db.commit()
        logger.info(f"HNSW index '{index_name}' created successfully on {table_name}.{column_name}")
    except Exception as e:
        logger.error(f"Error creating HNSW index: {e}")
        db.rollback()
        raise


def setup_all_vector_indexes(db: Session) -> None:
    """
    Set up all vector indexes for the application
    """
    logger.info("Setting up pgvector indexes...")

    try:
        # Ensure pgvector extension exists
        create_vector_extension(db)

        # Farm profile embeddings (512-dimensional)
        # Using HNSW for better accuracy in farm similarity matching
        create_hnsw_index(
            db, table_name="farms", column_name="farm_profile_embedding", m=16, ef_construction=64
        )

        # Crop variety embeddings (384-dimensional)
        # Using IVFFlat for faster search across many crop varieties
        create_ivfflat_index(db, table_name="crop_varieties", column_name="embedding", lists=100)

        # Crop recommendation embeddings (384-dimensional)
        # Using HNSW for accurate recommendation matching
        create_hnsw_index(
            db,
            table_name="crop_recommendations",
            column_name="rag_embedding",
            m=16,
            ef_construction=64,
        )

        logger.info("All pgvector indexes created successfully!")

    except Exception as e:
        logger.error(f"Error setting up vector indexes: {e}")
        raise


def drop_vector_index(db: Session, index_name: str) -> None:
    """
    Drop a vector index

    Args:
        db: Database session
        index_name: Name of the index to drop
    """
    try:
        query = text(f"DROP INDEX IF EXISTS {index_name}")
        db.execute(query)
        db.commit()
        logger.info(f"Index '{index_name}' dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping index: {e}")
        db.rollback()
        raise


def rebuild_vector_index(
    db: Session, table_name: str, column_name: str, index_type: str = "hnsw", **kwargs
) -> None:
    """
    Rebuild a vector index (drop and recreate)

    Args:
        db: Database session
        table_name: Name of the table
        column_name: Name of the vector column
        index_type: Type of index ('hnsw' or 'ivfflat')
        **kwargs: Additional parameters for index creation
    """
    index_name = f"idx_{table_name}_{column_name}_{index_type}"

    logger.info(f"Rebuilding index '{index_name}'...")

    # Drop existing index
    drop_vector_index(db, index_name)

    # Recreate index
    if index_type == "hnsw":
        create_hnsw_index(
            db,
            table_name=table_name,
            column_name=column_name,
            m=kwargs.get("m", 16),
            ef_construction=kwargs.get("ef_construction", 64),
            index_name=index_name,
        )
    elif index_type == "ivfflat":
        create_ivfflat_index(
            db,
            table_name=table_name,
            column_name=column_name,
            lists=kwargs.get("lists", 100),
            index_name=index_name,
        )
    else:
        raise ValueError(f"Unknown index type: {index_type}")

    logger.info(f"Index '{index_name}' rebuilt successfully")


def get_vector_index_stats(db: Session, table_name: str) -> dict:
    """
    Get statistics about vector indexes on a table

    Args:
        db: Database session
        table_name: Name of the table

    Returns:
        dict: Index statistics
    """
    try:
        query = text(f"""
            SELECT
                indexname,
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
            FROM pg_indexes
            WHERE tablename = :table_name
            AND indexname LIKE 'idx_%vector%'
        """)

        result = db.execute(query, {"table_name": table_name})
        indexes = []

        for row in result:
            indexes.append({"name": row[0], "definition": row[1], "size": row[2]})

        return {"table": table_name, "indexes": indexes, "count": len(indexes)}

    except Exception as e:
        logger.error(f"Error getting index stats: {e}")
        return {"error": str(e)}


def optimize_vector_search_settings(db: Session) -> None:
    """
    Optimize PostgreSQL settings for vector search
    """
    try:
        # Set effective_cache_size for better query planning
        db.execute(text("SET effective_cache_size = '4GB'"))

        # Set maintenance_work_mem for faster index creation
        db.execute(text("SET maintenance_work_mem = '1GB'"))

        # Set work_mem for query execution
        db.execute(text("SET work_mem = '256MB'"))

        # For IVFFlat: set probes for search accuracy
        # Higher probes = more accurate but slower
        db.execute(text("SET ivfflat.probes = 10"))

        db.commit()
        logger.info("Vector search settings optimized")

    except Exception as e:
        logger.error(f"Error optimizing settings: {e}")
        db.rollback()


def main():
    """
    Main function to set up all vector indexes
    """
    logger.info("=== Vector Index Setup Started ===")

    db = SessionLocal()

    try:
        # Set up all vector indexes
        setup_all_vector_indexes(db)

        # Optimize settings
        optimize_vector_search_settings(db)

        # Print statistics
        for table in ["farms", "crop_varieties", "crop_recommendations"]:
            stats = get_vector_index_stats(db, table)
            logger.info(f"Index stats for {table}: {stats}")

        logger.info("=== Vector Index Setup Completed Successfully ===")

    except Exception as e:
        logger.error(f"Vector index setup failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
