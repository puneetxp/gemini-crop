"""
BigQuery service for streaming app events, crop audits, and marketplace metrics.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

from app.core.config import settings

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service to stream application events and metrics to BigQuery for analytics and Looker dashboards"""

    def __init__(self):
        self._client = None
        self._dataset_id = settings.BIGQUERY_DATASET
        self._init_client()

    def _init_client(self):
        try:
            # BigQuery will auto-authenticate using environment credentials
            self._client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            logger.info("BigQuery client initialized successfully")
        except Exception as e:
            logger.warning(f"BigQuery initialization failed: {e}. Running in fallback/mock mode.")
            self._client = None

    def log_event(self, table_name: str, row_data: Dict[str, Any]) -> bool:
        """
        Stream a single event row to a BigQuery table.
        Table names can include: 'farm_events', 'market_transactions', 'ai_queries', 'weather_warnings'.
        """
        # Ensure timestamp exists
        if "timestamp" not in row_data:
            row_data["timestamp"] = datetime.datetime.utcnow().isoformat()

        if not self._client:
            logger.info(f"Mock BigQuery log to '{table_name}': {row_data}")
            return True

        try:
            table_ref = self._client.dataset(self._dataset_id).table(table_name)
            errors = self._client.insert_rows_json(table_ref, [row_data])

            if errors:
                logger.error(f"BigQuery insert rows errors on table '{table_name}': {errors}")
                return False

            logger.debug(f"Logged event to BigQuery table '{table_name}' successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to log event to BigQuery table '{table_name}': {e}")
            return False

    def query_community_insights(
        self, state: str, district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate community-level decision intelligence data from BigQuery.

        Returns district/state-level metrics:
        - Top crops being cultivated
        - Average yield predictions
        - Active farm count
        - Pest/disease alert frequency
        - Community Wellness Score (0-100)

        Falls back to mock data if BigQuery is not configured.
        """
        if not self._client:
            logger.info(f"Mock community insights for state={state}, district={district}")
            return self._mock_community_insights(state, district)

        try:
            location_filter = f"state = '{state}'"
            if district:
                location_filter += f" AND district = '{district}'"

            query = f"""
            WITH crop_stats AS (
                SELECT
                    crop_name,
                    COUNT(*) as farm_count,
                    AVG(CAST(price_per_kg AS FLOAT64)) as avg_price
                FROM `{settings.GOOGLE_CLOUD_PROJECT}.{self._dataset_id}.farm_events`
                WHERE {location_filter}
                GROUP BY crop_name
                ORDER BY farm_count DESC
                LIMIT 5
            ),
            alert_stats AS (
                SELECT COUNT(*) as alert_count
                FROM `{settings.GOOGLE_CLOUD_PROJECT}.{self._dataset_id}.weather_warnings`
                WHERE {location_filter}
                AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            )
            SELECT
                (SELECT ARRAY_AGG(STRUCT(crop_name, farm_count, avg_price)) FROM crop_stats) as top_crops,
                (SELECT alert_count FROM alert_stats) as recent_alerts
            """

            query_job = self._client.query(query)
            results = list(query_job.result())

            if results:
                row = results[0]
                top_crops = row.get("top_crops") or []
                recent_alerts = row.get("recent_alerts") or 0

                # Compute a simple Community Wellness Score
                crop_diversity = min(len(top_crops) * 20, 40)  # Max 40 points for diversity
                alert_penalty = max(0, 30 - recent_alerts * 3)  # Max 30 points, minus 3 per alert
                activity_score = 30  # Base activity score

                wellness_score = min(crop_diversity + alert_penalty + activity_score, 100)

                return {
                    "state": state,
                    "district": district,
                    "top_crops": [dict(c) for c in top_crops] if top_crops else [],
                    "recent_pest_alerts": recent_alerts,
                    "community_wellness_score": wellness_score,
                    "data_source": "bigquery_live",
                }

        except Exception as e:
            logger.error(f"BigQuery community insights query failed: {e}")

        return self._mock_community_insights(state, district)

    def _mock_community_insights(
        self, state: str, district: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return realistic mock community data for development/demo."""
        return {
            "state": state,
            "district": district or "All Districts",
            "top_crops": [
                {"crop_name": "Rice (Paddy)", "farm_count": 1245, "avg_price": 22.5},
                {"crop_name": "Wheat", "farm_count": 987, "avg_price": 28.0},
                {"crop_name": "Cotton", "farm_count": 654, "avg_price": 65.0},
                {"crop_name": "Soybean", "farm_count": 432, "avg_price": 45.0},
                {"crop_name": "Sugarcane", "farm_count": 321, "avg_price": 3.5},
            ],
            "total_active_farms": 3639,
            "avg_farm_size_acres": 4.2,
            "recent_pest_alerts": 7,
            "top_pest_threats": ["Fall Armyworm", "Brown Plant Hopper", "Stem Borer"],
            "community_wellness_score": 72,
            "wellness_breakdown": {
                "crop_diversity": 40,
                "pest_resilience": 12,
                "market_activity": 20,
            },
            "data_source": "mock_development",
        }


# Singleton instance
bigquery_service = BigQueryService()
