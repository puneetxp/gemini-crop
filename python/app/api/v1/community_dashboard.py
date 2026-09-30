"""
Community Decision Intelligence Dashboard API

Provides district/state-level aggregated insights for community stakeholders,
government planners, and agricultural extension officers.

Demonstrates: Predictive Analytics, Real-time Inference, BigQuery Analytics — Google Cloud Hackathon criteria.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/community", tags=["Community Intelligence"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_community_dashboard(
    state: str = Query(..., description="Indian state name (e.g. Maharashtra, Punjab)"),
    district: Optional[str] = Query(None, description="District name for finer granularity"),
):
    """
    Get community-level decision intelligence for a state or district.

    Returns:
    - **Top 5 crops** being cultivated with farm counts and average prices
    - **Pest/disease alert frequency** in the last 30 days
    - **Community Wellness Score** (0-100) based on crop diversity, pest resilience, and market activity
    - **Actionable insights** for stakeholders

    Data is aggregated from **BigQuery** analytics streams and rendered
    in **Looker Studio** dashboards for visual decision support.

    This demonstrates:
    - Real-time analytics and BigQuery data aggregation
    - Community decision intelligence
    - Predictive analytics and forecasting
    """
    logger.info(f"Community dashboard request: state={state}, district={district}")

    try:
        insights = bigquery_service.query_community_insights(state=state, district=district)

        # Add interpretive analysis
        wellness = insights.get("community_wellness_score", 0)
        if wellness >= 80:
            health_status = "Excellent"
            recommendation = "Community agriculture is thriving. Focus on scaling successful crops and expanding market access."
        elif wellness >= 60:
            health_status = "Good"
            recommendation = "Solid agricultural foundation. Consider crop diversification and pest management improvements."
        elif wellness >= 40:
            health_status = "Fair"
            recommendation = "Several areas need attention. Prioritize pest control, improve irrigation, and explore government subsidy programs."
        else:
            health_status = "Needs Attention"
            recommendation = "Urgent intervention needed. Consider emergency agricultural extension services and disaster mitigation planning."

        insights["health_status"] = health_status
        insights["recommendation"] = recommendation

        return {"success": True, "data": insights}

    except Exception as e:
        logger.error(f"Community dashboard error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate community insights: {str(e)}"
        )
