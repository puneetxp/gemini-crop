"""
Soil Health Tracking API endpoints
Handles soil health tracking, trend analysis, and report generation

Task 22.3: Build soil health tracking system
"""

import io
import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.farm_access import farm_for_user, plot_for_user
from app.services.soil_health_report_service import soil_health_report_service
from app.services.soil_testing_service import soil_testing_service

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/soil-health", tags=["soil-health"], dependencies=[Depends(get_current_active_user)]
)


def _owned(farm_id: int, plot_id: Optional[int], user) -> None:
    """Owner check (raw SQL): the farm must be the user's, and the plot on that farm; 404 otherwise."""
    try:
        farm_for_user(farm_id, user)
        if plot_id is not None and plot_for_user(plot_id, user)["farm_id"] != farm_id:
            raise LookupError(f"Plot {plot_id} not found")
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Response schemas
class DegradationAlert(BaseModel):
    """Soil degradation alert"""

    parameter: str
    severity: str
    first_value: float
    last_value: float
    change_percent: float
    message: str


class DegradationAnalysis(BaseModel):
    """Soil degradation analysis response"""

    status: str = Field(..., description="Overall status: healthy/warning/critical")
    tests_analyzed: int
    period_days: int
    degradation_alerts: list[DegradationAlert]
    trends: dict
    first_test_date: date
    last_test_date: date


class PredictionResponse(BaseModel):
    """Soil health prediction response"""

    status: str
    prediction_date: Optional[date] = None
    months_ahead: Optional[int] = None
    predictions: dict
    tests_analyzed: Optional[int] = None
    message: Optional[str] = None


class ActionPlanResponse(BaseModel):
    """Soil improvement action plan response"""

    status: str
    test_date: Optional[date] = None
    current_soil_health_score: Optional[float] = None
    target_soil_health_score: Optional[float] = None
    immediate_actions: list[dict]
    short_term_actions: list[dict]
    medium_term_actions: list[dict]
    long_term_actions: list[dict]
    total_actions: int
    message: Optional[str] = None


class SoilHealthReport(BaseModel):
    """Comprehensive soil health report"""

    report_date: date
    farm_id: int
    plot_id: Optional[int]
    latest_test: dict
    history_summary: dict
    degradation_analysis: dict
    predictions: dict
    action_plan: dict
    charts: Optional[dict]


@router.get("/{plot_id}", response_model=SoilHealthReport)
async def get_soil_health_by_plot_alias(
    plot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Registry alias for soil health by plot"""
    # Find farm_id for this plot (owner-scoped)
    try:
        plot_result = plot_for_user(plot_id, current_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Plot not found")

    return await get_soil_health_report(
        plot_result.farm_id, plot_id, db=db, current_user=current_user
    )


@router.get("/farm/{farm_id}/degradation", response_model=DegradationAnalysis)
async def analyze_soil_degradation(
    farm_id: int,
    plot_id: Optional[int] = None,
    months_lookback: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Analyze soil degradation trends

    Identifies declining trends (> 10% decrease) over specified period.
    Generates alerts with severity levels (critical/high/warning).
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Analyzing soil degradation for farm {farm_id}")

        analysis = await soil_testing_service.detect_soil_degradation(
            db, farm_id, plot_id, months_lookback, user=current_user
        )

        if analysis["status"] == "insufficient_data":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=analysis["message"])

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing soil degradation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze soil degradation",
        )


@router.get("/farm/{farm_id}/predictions", response_model=PredictionResponse)
async def predict_soil_health(
    farm_id: int,
    plot_id: Optional[int] = None,
    months_ahead: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Predict future soil health using linear regression

    Analyzes historical trends and predicts future values for key parameters.
    Requires at least 3 historical soil tests.
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Predicting soil health for farm {farm_id}")

        predictions = await soil_testing_service.predict_future_soil_health(
            db, farm_id, plot_id, months_ahead, user=current_user
        )

        if predictions["status"] == "insufficient_data":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=predictions["message"]
            )

        return predictions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting soil health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict soil health",
        )


@router.get("/farm/{farm_id}/action-plan", response_model=ActionPlanResponse)
async def get_improvement_action_plan(
    farm_id: int,
    plot_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate prioritized soil improvement action plan

    Analyzes deficiency patterns and creates comprehensive improvement plan
    with timeline (immediate, short-term, medium-term, long-term actions).
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Generating action plan for farm {farm_id}")

        action_plan = await soil_testing_service.generate_improvement_action_plan(
            db, farm_id, plot_id, user=current_user
        )

        if action_plan["status"] == "no_data":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=action_plan["message"]
            )

        return action_plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating action plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate action plan",
        )


@router.get("/farm/{farm_id}/report", response_model=SoilHealthReport)
async def get_soil_health_report(
    farm_id: int,
    plot_id: Optional[int] = None,
    include_charts: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate comprehensive soil health report

    Includes:
    - Latest test results
    - Historical trends
    - Degradation analysis
    - Future predictions
    - Prioritized action plan
    - Trend charts (optional)
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Generating soil health report for farm {farm_id}")

        report = await soil_health_report_service.generate_soil_health_report(
            db, farm_id, plot_id, include_charts, user=current_user
        )

        if report.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=report.get("message", "No data available"),
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate soil health report",
        )


@router.get("/farm/{farm_id}/export/csv")
async def export_soil_history_csv(
    farm_id: int,
    plot_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Export soil test history as CSV

    Downloads complete soil test history in CSV format for external analysis.
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Exporting soil history as CSV for farm {farm_id}")

        csv_content = await soil_health_report_service.export_report_csv(
            db, farm_id, plot_id, user=current_user
        )

        # Create streaming response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=soil_history_farm_{farm_id}.csv"
            },
        )

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export soil history",
        )


@router.get("/farm/{farm_id}/export/pdf")
async def export_soil_report_pdf(
    farm_id: int,
    plot_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate and download PDF report

    Note: PDF generation is not yet implemented.
    This is a placeholder for future implementation.
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Generating PDF report for farm {farm_id}")

        # PDF generation not yet implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF generation will be implemented in future version. Use CSV export or JSON report for now.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        )


@router.get("/farm/{farm_id}/trends")
async def get_soil_trends(
    farm_id: int,
    plot_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get soil parameter trends over time

    Returns chart-ready data for visualizing soil health trends.
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Fetching soil trends for farm {farm_id}")

        # Get history
        history = await soil_testing_service.get_soil_test_history(
            db, farm_id, plot_id, limit=20, user=current_user
        )

        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No soil test data available"
            )

        # Generate chart data
        from app.services.soil_health_report_service import soil_health_report_service

        charts = soil_health_report_service._generate_chart_data(history)

        return {
            "farm_id": farm_id,
            "plot_id": plot_id,
            "tests_count": len(history),
            "charts": charts,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch soil trends"
        )
