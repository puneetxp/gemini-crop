"""
Soil Health Report Generation Service
Generates comprehensive PDF reports with trend analysis and recommendations

Task 22.3: Build soil health tracking system
"""

import io
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SoilHealthReportService:
    """Service for generating soil health reports"""

    def __init__(self):
        """Initialize report service"""
        pass

    async def generate_soil_health_report(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        include_charts: bool = True,
        user=None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive soil health report

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID
            include_charts: Whether to include trend charts

        Returns:
            Report data structure (PDF generation to be implemented)
        """
        from app.services.soil_testing_service import _load_soil_tests, soil_testing_service

        logger.info(f"Generating soil health report for farm {farm_id}")

        # Get latest test (raw SQL via app.core.db.DB; owner-checked when `user` is given)
        latest = _load_soil_tests(farm_id, plot_id, newest_first=True, limit=1, user=user)
        latest_test = latest[0] if latest else None

        if not latest_test:
            return {"status": "error", "message": "No soil test data available"}

        # Get test history
        history = await soil_testing_service.get_soil_test_history(
            db, farm_id, plot_id, limit=10, user=user
        )

        # Get degradation analysis
        degradation = await soil_testing_service.detect_soil_degradation(
            db, farm_id, plot_id, user=user
        )

        # Get predictions
        predictions = await soil_testing_service.predict_future_soil_health(
            db, farm_id, plot_id, user=user
        )

        # Get action plan
        action_plan = await soil_testing_service.generate_improvement_action_plan(
            db, farm_id, plot_id, user=user
        )

        # Build report structure
        report = {
            "report_date": date.today(),
            "farm_id": farm_id,
            "plot_id": plot_id,
            "latest_test": {
                "test_date": latest_test.test_date,
                "soil_health_score": latest_test.soil_health_score,
                "lab_name": latest_test.lab_name,
                "parameters": {
                    "nitrogen_kg_per_ha": latest_test.nitrogen_kg_per_ha,
                    "phosphorus_kg_per_ha": latest_test.phosphorus_kg_per_ha,
                    "potassium_kg_per_ha": latest_test.potassium_kg_per_ha,
                    "ph_level": latest_test.ph_level,
                    "organic_carbon_percent": latest_test.organic_carbon_percent,
                    "electrical_conductivity": latest_test.electrical_conductivity,
                },
            },
            "history_summary": {
                "total_tests": len(history),
                "first_test_date": history[-1]["test_date"] if history else None,
                "latest_test_date": history[0]["test_date"] if history else None,
            },
            "degradation_analysis": degradation,
            "predictions": predictions,
            "action_plan": action_plan,
            "charts": self._generate_chart_data(history) if include_charts else None,
        }

        logger.info("Soil health report generated successfully")
        return report

    def _generate_chart_data(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate chart data for trend visualization

        Args:
            history: List of soil test results

        Returns:
            Chart data structure
        """
        if not history:
            return {}

        # Prepare data for charts
        dates = [test["test_date"].isoformat() for test in reversed(history)]

        charts = {
            "soil_health_score": {
                "labels": dates,
                "data": [test.get("soil_health_score") for test in reversed(history)],
                "title": "Soil Health Score Trend",
            },
            "npk_levels": {
                "labels": dates,
                "nitrogen": [test.get("nitrogen_kg_per_ha") for test in reversed(history)],
                "phosphorus": [test.get("phosphorus_kg_per_ha") for test in reversed(history)],
                "potassium": [test.get("potassium_kg_per_ha") for test in reversed(history)],
                "title": "N-P-K Levels Over Time",
            },
            "ph_trend": {
                "labels": dates,
                "data": [test.get("ph_level") for test in reversed(history)],
                "title": "pH Level Trend",
                "optimal_range": [6.0, 7.5],
            },
            "organic_carbon": {
                "labels": dates,
                "data": [test.get("organic_carbon_percent") for test in reversed(history)],
                "title": "Organic Carbon Trend",
                "optimal_range": [0.5, 0.75],
            },
        }

        return charts

    async def export_report_csv(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        user=None,
    ) -> str:
        """
        Export soil test history as CSV

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID

        Returns:
            CSV string
        """
        from app.services.soil_testing_service import soil_testing_service

        logger.info(f"Exporting soil test history as CSV for farm {farm_id}")

        # Get history
        history = await soil_testing_service.get_soil_test_history(
            db, farm_id, plot_id, limit=100, user=user
        )

        if not history:
            return "No data available"

        # Build CSV
        csv_lines = []

        # Header
        headers = [
            "Test Date",
            "Lab Name",
            "Soil Health Score",
            "Nitrogen (kg/ha)",
            "Phosphorus (kg/ha)",
            "Potassium (kg/ha)",
            "pH Level",
            "Organic Carbon (%)",
            "EC (dS/m)",
            "Zinc (ppm)",
            "Iron (ppm)",
            "Manganese (ppm)",
        ]
        csv_lines.append(",".join(headers))

        # Data rows
        for test in history:
            row = [
                str(test.get("test_date", "")),
                test.get("lab_name", ""),
                str(test.get("soil_health_score", "")),
                str(test.get("nitrogen_kg_per_ha", "")),
                str(test.get("phosphorus_kg_per_ha", "")),
                str(test.get("potassium_kg_per_ha", "")),
                str(test.get("ph_level", "")),
                str(test.get("organic_carbon_percent", "")),
                str(test.get("electrical_conductivity", "")),
                str(test.get("zinc_ppm", "")),
                str(test.get("iron_ppm", "")),
                str(test.get("manganese_ppm", "")),
            ]
            csv_lines.append(",".join(row))

        csv_content = "\n".join(csv_lines)
        logger.info(f"Exported {len(history)} soil test results as CSV")

        return csv_content

    async def generate_pdf_report(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        user=None,
    ) -> bytes:
        """
        Generate PDF report (placeholder for future implementation)

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID

        Returns:
            PDF bytes
        """
        logger.info(f"Generating PDF report for farm {farm_id}")

        # TODO: Implement PDF generation using reportlab or weasyprint
        # This would involve:
        # 1. Get report data
        # 2. Create PDF with charts and tables
        # 3. Add recommendations and action plan
        # 4. Return PDF bytes

        raise NotImplementedError("PDF generation will be implemented in future version")


# Singleton instance
soil_health_report_service = SoilHealthReportService()
