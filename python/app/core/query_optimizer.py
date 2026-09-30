"""
Database Query Optimization Utilities
Provides helpers for optimizing SQLAlchemy queries with eager loading and indexing
"""

import logging
from typing import Any, List, Optional

from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, joinedload, selectinload, subqueryload

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Utility class for optimizing database queries

    Features:
    - Eager loading helpers
    - Index creation
    - Query analysis
    - N+1 query prevention
    """

    @staticmethod
    def add_eager_loading(
        query: Query, relationships: List[str], strategy: str = "joined"
    ) -> Query:
        """
        Add eager loading to query to prevent N+1 queries

        Args:
            query: SQLAlchemy query
            relationships: List of relationship names to eager load
            strategy: Loading strategy ("joined", "selectin", "subquery")

        Returns:
            Query with eager loading applied
        """
        if strategy == "joined":
            loader = joinedload
        elif strategy == "selectin":
            loader = selectinload
        elif strategy == "subquery":
            loader = subqueryload
        else:
            raise ValueError(f"Invalid loading strategy: {strategy}")

        for relationship in relationships:
            query = query.options(loader(relationship))

        return query

    @staticmethod
    async def create_indexes(session: AsyncSession, indexes: List[dict]):
        """
        Create database indexes for common query patterns

        Args:
            session: Database session
            indexes: List of index definitions
                [
                    {
                        "name": "idx_farms_farmer_id",
                        "table": "farms",
                        "columns": ["farmer_id"]
                    },
                    ...
                ]
        """
        for index_def in indexes:
            try:
                name = index_def["name"]
                table = index_def["table"]
                columns = index_def["columns"]
                unique = index_def.get("unique", False)

                # Build CREATE INDEX statement
                unique_str = "UNIQUE " if unique else ""
                columns_str = ", ".join(columns)

                sql = f"""
                CREATE INDEX IF NOT EXISTS {name}
                ON {table} ({columns_str})
                """

                await session.execute(text(sql))
                logger.info(f"Created index {name} on {table}({columns_str})")

            except Exception as e:
                logger.error(f"Error creating index {index_def.get('name')}: {e}")

    @staticmethod
    def get_common_indexes() -> List[dict]:
        """
        Get list of common indexes for the application

        Returns:
            List of index definitions
        """
        return [
            # Farm indexes
            {"name": "idx_farms_farmer_id", "table": "farms", "columns": ["farmer_id"]},
            {
                "name": "idx_farms_state_district",
                "table": "farms",
                "columns": ["state", "district"],
            },
            # Marketplace listing indexes
            {
                "name": "idx_marketplace_listings_farmer_id",
                "table": "marketplace_listings",
                "columns": ["farmer_id"],
            },
            {
                "name": "idx_marketplace_listings_crop_type",
                "table": "marketplace_listings",
                "columns": ["crop_type"],
            },
            {
                "name": "idx_marketplace_listings_state_district",
                "table": "marketplace_listings",
                "columns": ["location_state", "location_district"],
            },
            {
                "name": "idx_marketplace_listings_harvest_date",
                "table": "marketplace_listings",
                "columns": ["expected_harvest_date"],
            },
            {
                "name": "idx_marketplace_listings_status",
                "table": "marketplace_listings",
                "columns": ["status"],
            },
            # Annual strategy indexes
            {
                "name": "idx_annual_strategies_farmer_id",
                "table": "annual_strategies",
                "columns": ["farmer_id"],
            },
            {
                "name": "idx_annual_strategies_farm_id",
                "table": "annual_strategies",
                "columns": ["farm_id"],
            },
            {
                "name": "idx_annual_strategies_year",
                "table": "annual_strategies",
                "columns": ["year"],
            },
            {
                "name": "idx_annual_strategies_status",
                "table": "annual_strategies",
                "columns": ["status"],
            },
            # Crop indexes
            {"name": "idx_crops_farm_id", "table": "crops", "columns": ["farm_id"]},
            {"name": "idx_crops_plot_id", "table": "crops", "columns": ["plot_id"]},
            {
                "name": "idx_crops_harvest_date",
                "table": "crops",
                "columns": ["expected_harvest_date"],
            },
            # Buyer interest indexes
            {
                "name": "idx_buyer_interests_listing_id",
                "table": "buyer_interests",
                "columns": ["listing_id"],
            },
            {
                "name": "idx_buyer_interests_buyer_id",
                "table": "buyer_interests",
                "columns": ["buyer_id"],
            },
            {
                "name": "idx_buyer_interests_status",
                "table": "buyer_interests",
                "columns": ["status"],
            },
            # Crop market data indexes
            {
                "name": "idx_crop_market_data_crop_type",
                "table": "crop_market_data",
                "columns": ["crop_type"],
            },
            {
                "name": "idx_crop_market_data_state_district",
                "table": "crop_market_data",
                "columns": ["state", "district"],
            },
            {
                "name": "idx_crop_market_data_year_month",
                "table": "crop_market_data",
                "columns": ["year", "month"],
            },
            # Weather alert indexes
            {
                "name": "idx_weather_alerts_state_district",
                "table": "weather_alerts",
                "columns": ["state", "district"],
            },
            {
                "name": "idx_weather_alerts_severity",
                "table": "weather_alerts",
                "columns": ["severity"],
            },
            {
                "name": "idx_weather_alerts_valid_until",
                "table": "weather_alerts",
                "columns": ["valid_until"],
            },
        ]


# Eager loading presets for common queries
EAGER_LOADING_PRESETS = {
    "farm_with_plots": {"relationships": ["plots"], "strategy": "selectin"},
    "farm_with_user": {"relationships": ["user"], "strategy": "joined"},
    "listing_with_farm_and_user": {"relationships": ["farm", "user"], "strategy": "joined"},
    "listing_with_buyer_interests": {"relationships": ["buyer_interests"], "strategy": "selectin"},
    "strategy_with_farm": {"relationships": ["farm"], "strategy": "joined"},
}


def apply_eager_loading_preset(query: Query, preset_name: str) -> Query:
    """
    Apply eager loading preset to query

    Args:
        query: SQLAlchemy query
        preset_name: Name of preset from EAGER_LOADING_PRESETS

    Returns:
        Query with eager loading applied
    """
    if preset_name not in EAGER_LOADING_PRESETS:
        logger.warning(f"Unknown eager loading preset: {preset_name}")
        return query

    preset = EAGER_LOADING_PRESETS[preset_name]
    return QueryOptimizer.add_eager_loading(query, preset["relationships"], preset["strategy"])
