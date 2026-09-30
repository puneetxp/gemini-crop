"""
Soil Testing Laboratory Integration Service
Handles ICAR soil testing lab integration, soil test result parsing, and soil health score calculation

Task 22.1: Integrate with soil testing laboratories
Task 22.3: Build soil health tracking system
"""

import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any  # db args are kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional, Tuple

from app.services.farm_access import farm_for_user, fetch_all, plot_for_user

logger = logging.getLogger(__name__)


def _as_date(value):
    """soil_test_results.test_date is a timestamp column; the analysis code works in dates."""
    return value.date() if isinstance(value, datetime) else value


def _load_soil_tests(
    farm_id: int,
    plot_id: Optional[int] = None,
    since: Optional[date] = None,
    newest_first: bool = True,
    limit: Optional[int] = None,
    user=None,
) -> List[Any]:
    """Soil test rows for a farm (owner-checked when `user` is given), as attribute-access rows."""
    if user is not None:
        farm_for_user(farm_id, user)
        if plot_id and plot_for_user(plot_id, user)["farm_id"] != farm_id:
            raise LookupError(f"Plot {plot_id} not found")
    where, bind = ["farm_id = ?"], [farm_id]
    if plot_id:
        where.append("plot_id = ?")
        bind.append(plot_id)
    if since:
        where.append("test_date >= ?")
        bind.append(since)
    sql = (
        f"SELECT * FROM soil_test_results WHERE {' AND '.join(where)} "
        f"ORDER BY test_date {'DESC' if newest_first else 'ASC'}, id {'DESC' if newest_first else 'ASC'}"
    )
    if limit:
        sql += " LIMIT ?"
        bind.append(int(limit))
    tests = fetch_all(sql, bind)
    for t in tests:
        t.test_date = _as_date(t.test_date)
    return tests


class SoilTestingService:
    """Service for soil testing laboratory integration and soil health analysis"""

    # Optimal ranges for soil parameters (based on ICAR guidelines)
    OPTIMAL_RANGES = {
        "ph_level": {"min": 6.0, "max": 7.5, "weight": 0.20},
        "organic_carbon_percent": {"min": 0.5, "max": 0.75, "weight": 0.15},
        "nitrogen_kg_per_ha": {"min": 280, "max": 560, "weight": 0.15},
        "phosphorus_kg_per_ha": {"min": 22, "max": 56, "weight": 0.15},
        "potassium_kg_per_ha": {"min": 280, "max": 560, "weight": 0.15},
        "electrical_conductivity": {"min": 0.0, "max": 1.0, "weight": 0.10},
        "zinc_ppm": {"min": 0.6, "max": 1.2, "weight": 0.03},
        "iron_ppm": {"min": 4.5, "max": 10.0, "weight": 0.02},
        "manganese_ppm": {"min": 2.0, "max": 5.0, "weight": 0.02},
        "copper_ppm": {"min": 0.2, "max": 0.5, "weight": 0.02},
        "boron_ppm": {"min": 0.5, "max": 1.0, "weight": 0.01},
    }

    def __init__(self):
        """Initialize soil testing service"""
        # ICAR API configuration (placeholder - actual API details would be configured here)
        self.icar_api_base_url = "https://api.icar.gov.in/soil-testing"  # Placeholder
        self.icar_api_key = None  # Would be loaded from settings

    async def fetch_soil_test_from_icar(
        self, lab_reference_number: str, lab_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch soil test results from ICAR laboratory API

        Note: This is a placeholder implementation. Actual ICAR API integration
        would require official API credentials and documentation.

        Args:
            lab_reference_number: Laboratory reference/report number
            lab_name: Optional laboratory name for routing

        Returns:
            Soil test data dictionary or None if not found
        """
        logger.info(f"Fetching soil test from ICAR: {lab_reference_number}")

        # TODO: Implement actual ICAR API integration when API is available
        # This would involve:
        # 1. Authentication with ICAR API
        # 2. Making HTTP request to fetch test results
        # 3. Parsing response and mapping to our schema

        # Placeholder response structure
        logger.warning("ICAR API integration not yet implemented - using placeholder")
        return None

    def parse_soil_test_manual_entry(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse manually entered soil test data

        Args:
            test_data: Dictionary with soil test parameters

        Returns:
            Validated and normalized soil test data
        """
        logger.info("Parsing manual soil test entry")

        parsed_data = {}

        # Parse and validate each parameter
        if "nitrogen_kg_per_ha" in test_data and test_data["nitrogen_kg_per_ha"] is not None:
            parsed_data["nitrogen_kg_per_ha"] = float(test_data["nitrogen_kg_per_ha"])

        if "phosphorus_kg_per_ha" in test_data and test_data["phosphorus_kg_per_ha"] is not None:
            parsed_data["phosphorus_kg_per_ha"] = float(test_data["phosphorus_kg_per_ha"])

        if "potassium_kg_per_ha" in test_data and test_data["potassium_kg_per_ha"] is not None:
            parsed_data["potassium_kg_per_ha"] = float(test_data["potassium_kg_per_ha"])

        if "ph_level" in test_data and test_data["ph_level"] is not None:
            ph = float(test_data["ph_level"])
            if 0 <= ph <= 14:
                parsed_data["ph_level"] = ph
            else:
                raise ValueError("pH level must be between 0 and 14")

        if (
            "organic_carbon_percent" in test_data
            and test_data["organic_carbon_percent"] is not None
        ):
            parsed_data["organic_carbon_percent"] = float(test_data["organic_carbon_percent"])

        if (
            "organic_matter_percent" in test_data
            and test_data["organic_matter_percent"] is not None
        ):
            parsed_data["organic_matter_percent"] = float(test_data["organic_matter_percent"])

        if (
            "electrical_conductivity" in test_data
            and test_data["electrical_conductivity"] is not None
        ):
            parsed_data["electrical_conductivity"] = float(test_data["electrical_conductivity"])

        # Micronutrients
        for nutrient in [
            "sulfur_ppm",
            "zinc_ppm",
            "iron_ppm",
            "manganese_ppm",
            "copper_ppm",
            "boron_ppm",
        ]:
            if nutrient in test_data and test_data[nutrient] is not None:
                parsed_data[nutrient] = float(test_data[nutrient])

        # Metadata
        if "lab_name" in test_data:
            parsed_data["lab_name"] = test_data["lab_name"]

        if "lab_reference_number" in test_data:
            parsed_data["lab_reference_number"] = test_data["lab_reference_number"]

        if "test_method" in test_data:
            parsed_data["test_method"] = test_data["test_method"]

        if "recommendations" in test_data:
            parsed_data["recommendations"] = test_data["recommendations"]

        if "notes" in test_data:
            parsed_data["notes"] = test_data["notes"]

        logger.info(f"Parsed {len(parsed_data)} soil test parameters")
        return parsed_data

    def parse_soil_test_pdf(
        self, pdf_content: bytes, lab_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse soil test results from PDF document

        Note: This is a placeholder for PDF parsing functionality.
        Actual implementation would use PDF parsing libraries and OCR.

        Args:
            pdf_content: PDF file content as bytes
            lab_name: Laboratory name for format-specific parsing

        Returns:
            Extracted soil test data
        """
        logger.info(f"Parsing soil test PDF from lab: {lab_name}")

        # TODO: Implement PDF parsing
        # This would involve:
        # 1. Using PyPDF2 or pdfplumber to extract text
        # 2. Using regex patterns to extract numeric values
        # 3. Lab-specific parsing logic based on report formats
        # 4. OCR for scanned PDFs using pytesseract

        logger.warning("PDF parsing not yet implemented")
        raise NotImplementedError("PDF parsing will be implemented in future version")

    def calculate_soil_health_score(self, soil_data: Dict[str, Any]) -> float:
        """
        Calculate comprehensive soil health score (0-100 scale)

        Algorithm:
        - Each parameter is scored based on how close it is to optimal range
        - Scores are weighted based on parameter importance
        - Final score is sum of weighted scores

        Args:
            soil_data: Dictionary with soil test parameters

        Returns:
            Soil health score (0-100)
        """
        logger.info("Calculating soil health score")

        total_score = 0.0
        total_weight = 0.0
        scores_breakdown = {}

        for param, ranges in self.OPTIMAL_RANGES.items():
            if param in soil_data and soil_data[param] is not None:
                value = float(soil_data[param])
                optimal_min = ranges["min"]
                optimal_max = ranges["max"]
                weight = ranges["weight"]

                # Calculate parameter score (0-100)
                if optimal_min <= value <= optimal_max:
                    # Value is in optimal range - full score
                    param_score = 100.0
                elif value < optimal_min:
                    # Value is below optimal - score decreases with distance
                    # Allow 50% below optimal to still get some score
                    lower_bound = optimal_min * 0.5
                    if value >= lower_bound:
                        param_score = 50.0 + 50.0 * (value - lower_bound) / (
                            optimal_min - lower_bound
                        )
                    else:
                        param_score = 50.0 * (value / lower_bound) if value > 0 else 0.0
                else:
                    # Value is above optimal - score decreases with distance
                    # Allow 50% above optimal to still get some score
                    upper_bound = optimal_max * 1.5
                    if value <= upper_bound:
                        param_score = 50.0 + 50.0 * (upper_bound - value) / (
                            upper_bound - optimal_max
                        )
                    else:
                        param_score = 50.0 * (upper_bound / value) if value > 0 else 0.0

                # Apply weight
                weighted_score = param_score * weight
                total_score += weighted_score
                total_weight += weight

                scores_breakdown[param] = {
                    "value": value,
                    "optimal_range": f"{optimal_min}-{optimal_max}",
                    "score": round(param_score, 2),
                    "weighted_score": round(weighted_score, 2),
                }

        # Normalize to 0-100 scale
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0

        logger.info(f"Soil health score calculated: {final_score:.2f}/100")
        logger.debug(f"Score breakdown: {scores_breakdown}")

        return round(final_score, 2)

    def generate_soil_improvement_recommendations(
        self, soil_data: Dict[str, Any], soil_health_score: float
    ) -> List[Dict[str, Any]]:
        """
        Generate soil improvement recommendations based on test results

        Args:
            soil_data: Soil test data
            soil_health_score: Calculated soil health score

        Returns:
            List of recommendations with priority and actions
        """
        logger.info("Generating soil improvement recommendations")

        recommendations = []

        # pH recommendations
        if "ph_level" in soil_data and soil_data["ph_level"] is not None:
            ph = soil_data["ph_level"]
            if ph < 5.5:
                recommendations.append(
                    {
                        "priority": "high",
                        "parameter": "pH Level",
                        "current_value": ph,
                        "issue": "Soil is too acidic",
                        "recommendation": "Apply agricultural lime (calcium carbonate) at 2-4 tons per hectare",
                        "expected_improvement": "Increase pH to 6.0-7.0 range",
                        "timeline": "3-6 months",
                    }
                )
            elif ph > 8.5:
                recommendations.append(
                    {
                        "priority": "high",
                        "parameter": "pH Level",
                        "current_value": ph,
                        "issue": "Soil is too alkaline",
                        "recommendation": "Apply elemental sulfur or gypsum at 500-1000 kg per hectare",
                        "expected_improvement": "Decrease pH to 6.5-7.5 range",
                        "timeline": "6-12 months",
                    }
                )

        # Organic carbon recommendations
        if (
            "organic_carbon_percent" in soil_data
            and soil_data["organic_carbon_percent"] is not None
        ):
            oc = soil_data["organic_carbon_percent"]
            if oc < 0.4:
                recommendations.append(
                    {
                        "priority": "high",
                        "parameter": "Organic Carbon",
                        "current_value": oc,
                        "issue": "Low organic matter content",
                        "recommendation": "Add farmyard manure (10-15 tons/ha) or compost (5-7 tons/ha) annually",
                        "expected_improvement": "Increase organic carbon to 0.5-0.75%",
                        "timeline": "1-2 years",
                    }
                )

        # Nitrogen recommendations
        if "nitrogen_kg_per_ha" in soil_data and soil_data["nitrogen_kg_per_ha"] is not None:
            n = soil_data["nitrogen_kg_per_ha"]
            if n < 200:
                recommendations.append(
                    {
                        "priority": "medium",
                        "parameter": "Nitrogen",
                        "current_value": n,
                        "issue": "Low nitrogen content",
                        "recommendation": "Apply urea (120-150 kg/ha) or use green manure crops",
                        "expected_improvement": "Increase nitrogen to 280-560 kg/ha",
                        "timeline": "1 season",
                    }
                )

        # Phosphorus recommendations
        if "phosphorus_kg_per_ha" in soil_data and soil_data["phosphorus_kg_per_ha"] is not None:
            p = soil_data["phosphorus_kg_per_ha"]
            if p < 15:
                recommendations.append(
                    {
                        "priority": "medium",
                        "parameter": "Phosphorus",
                        "current_value": p,
                        "issue": "Low phosphorus content",
                        "recommendation": "Apply DAP (Di-ammonium phosphate) at 100-125 kg/ha",
                        "expected_improvement": "Increase phosphorus to 22-56 kg/ha",
                        "timeline": "1 season",
                    }
                )

        # Potassium recommendations
        if "potassium_kg_per_ha" in soil_data and soil_data["potassium_kg_per_ha"] is not None:
            k = soil_data["potassium_kg_per_ha"]
            if k < 200:
                recommendations.append(
                    {
                        "priority": "medium",
                        "parameter": "Potassium",
                        "current_value": k,
                        "issue": "Low potassium content",
                        "recommendation": "Apply Muriate of Potash (MOP) at 60-80 kg/ha",
                        "expected_improvement": "Increase potassium to 280-560 kg/ha",
                        "timeline": "1 season",
                    }
                )

        # Zinc deficiency (common in Indian soils)
        if "zinc_ppm" in soil_data and soil_data["zinc_ppm"] is not None:
            zn = soil_data["zinc_ppm"]
            if zn < 0.5:
                recommendations.append(
                    {
                        "priority": "medium",
                        "parameter": "Zinc",
                        "current_value": zn,
                        "issue": "Zinc deficiency",
                        "recommendation": "Apply zinc sulfate at 25 kg/ha or foliar spray of 0.5% ZnSO4",
                        "expected_improvement": "Increase zinc to 0.6-1.2 ppm",
                        "timeline": "1 season",
                    }
                )

        # Electrical conductivity (salinity)
        if (
            "electrical_conductivity" in soil_data
            and soil_data["electrical_conductivity"] is not None
        ):
            ec = soil_data["electrical_conductivity"]
            if ec > 2.0:
                recommendations.append(
                    {
                        "priority": "high",
                        "parameter": "Electrical Conductivity",
                        "current_value": ec,
                        "issue": "High soil salinity",
                        "recommendation": "Improve drainage, apply gypsum (2-5 tons/ha), and leach salts with irrigation",
                        "expected_improvement": "Reduce EC to below 1.0 dS/m",
                        "timeline": "6-12 months",
                    }
                )

        # Overall health recommendation
        if soil_health_score < 50:
            recommendations.insert(
                0,
                {
                    "priority": "critical",
                    "parameter": "Overall Soil Health",
                    "current_value": soil_health_score,
                    "issue": "Poor overall soil health",
                    "recommendation": "Implement comprehensive soil improvement program with organic matter addition, balanced fertilization, and crop rotation",
                    "expected_improvement": "Improve soil health score to above 60",
                    "timeline": "1-2 years",
                },
            )
        elif soil_health_score < 70:
            recommendations.insert(
                0,
                {
                    "priority": "medium",
                    "parameter": "Overall Soil Health",
                    "current_value": soil_health_score,
                    "issue": "Moderate soil health",
                    "recommendation": "Continue regular organic matter addition and balanced fertilization",
                    "expected_improvement": "Improve soil health score to above 75",
                    "timeline": "6-12 months",
                },
            )

        logger.info(f"Generated {len(recommendations)} soil improvement recommendations")
        return recommendations

    def compare_soil_tests(
        self, previous_test: Dict[str, Any], current_test: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two soil tests to track changes over time

        Args:
            previous_test: Previous soil test data
            current_test: Current soil test data

        Returns:
            Comparison analysis with trends
        """
        logger.info("Comparing soil tests for trend analysis")

        changes = {}

        # Compare each parameter
        for param in self.OPTIMAL_RANGES.keys():
            if param in previous_test and param in current_test:
                if previous_test[param] is not None and current_test[param] is not None:
                    prev_value = float(previous_test[param])
                    curr_value = float(current_test[param])
                    change = curr_value - prev_value
                    percent_change = (change / prev_value * 100) if prev_value != 0 else 0

                    # Determine trend
                    if abs(percent_change) < 5:
                        trend = "stable"
                    elif change > 0:
                        trend = "improving" if param != "electrical_conductivity" else "worsening"
                    else:
                        trend = "declining" if param != "electrical_conductivity" else "improving"

                    changes[param] = {
                        "previous_value": prev_value,
                        "current_value": curr_value,
                        "change": round(change, 2),
                        "percent_change": round(percent_change, 2),
                        "trend": trend,
                    }

        # Compare soil health scores
        if "soil_health_score" in previous_test and "soil_health_score" in current_test:
            prev_score = previous_test["soil_health_score"]
            curr_score = current_test["soil_health_score"]
            if prev_score is not None and curr_score is not None:
                score_change = curr_score - prev_score
                changes["soil_health_score"] = {
                    "previous_value": prev_score,
                    "current_value": curr_score,
                    "change": round(score_change, 2),
                    "trend": (
                        "improving"
                        if score_change > 5
                        else ("declining" if score_change < -5 else "stable")
                    ),
                }

        logger.info(f"Compared {len(changes)} soil parameters")
        return changes

    async def get_soil_test_history(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        limit: int = 10,
        user=None,
    ) -> List[Dict[str, Any]]:
        """
        Get soil test history for a farm or plot

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID
            limit: Maximum number of results

        Returns:
            List of soil test results ordered by date (newest first)
        """
        logger.info(f"Fetching soil test history for farm {farm_id}")

        tests = _load_soil_tests(farm_id, plot_id, newest_first=True, limit=limit, user=user)

        # Convert to dict
        history = []
        for test in tests:
            test_dict = {
                "id": test.id,
                "farm_id": test.farm_id,
                "plot_id": test.plot_id,
                "test_date": test.test_date,
                "lab_name": test.lab_name,
                "lab_reference_number": test.lab_reference_number,
                "nitrogen_kg_per_ha": test.nitrogen_kg_per_ha,
                "phosphorus_kg_per_ha": test.phosphorus_kg_per_ha,
                "potassium_kg_per_ha": test.potassium_kg_per_ha,
                "ph_level": test.ph_level,
                "organic_carbon_percent": test.organic_carbon_percent,
                "organic_matter_percent": test.organic_matter_percent,
                "electrical_conductivity": test.electrical_conductivity,
                "sulfur_ppm": test.sulfur_ppm,
                "zinc_ppm": test.zinc_ppm,
                "iron_ppm": test.iron_ppm,
                "manganese_ppm": test.manganese_ppm,
                "copper_ppm": test.copper_ppm,
                "boron_ppm": test.boron_ppm,
                "soil_health_score": test.soil_health_score,
                "test_method": test.test_method,
                "recommendations": test.recommendations,
                "notes": test.notes,
                "created_at": test.created_at,
                "updated_at": test.updated_at,
            }
            history.append(test_dict)

        logger.info(f"Found {len(history)} soil test results")
        return history

    async def detect_soil_degradation(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        months_lookback: int = 6,
        user=None,
    ) -> Dict[str, Any]:
        """
        Detect soil degradation by analyzing trends over time

        Identifies declining trends (> 10% decrease over specified period)

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID
            months_lookback: Number of months to analyze

        Returns:
            Degradation analysis with alerts
        """
        logger.info(f"Detecting soil degradation for farm {farm_id}")

        # Get tests from specified period
        cutoff_date = date.today() - timedelta(days=months_lookback * 30)

        tests = _load_soil_tests(farm_id, plot_id, since=cutoff_date, newest_first=False, user=user)

        if len(tests) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 soil tests to detect degradation",
                "tests_found": len(tests),
            }

        # Analyze trends for each parameter
        degradation_alerts = []
        trends = {}

        first_test = tests[0]
        last_test = tests[-1]

        for param in [
            "nitrogen_kg_per_ha",
            "phosphorus_kg_per_ha",
            "potassium_kg_per_ha",
            "ph_level",
            "organic_carbon_percent",
            "soil_health_score",
        ]:
            first_value = getattr(first_test, param)
            last_value = getattr(last_test, param)

            if first_value is not None and last_value is not None and first_value > 0:
                change_percent = ((last_value - first_value) / first_value) * 100

                # For pH, check if moving away from optimal range (6.0-7.5)
                if param == "ph_level":
                    optimal_mid = 6.75
                    first_deviation = abs(first_value - optimal_mid)
                    last_deviation = abs(last_value - optimal_mid)
                    is_degrading = last_deviation > first_deviation * 1.1
                else:
                    # For other parameters, declining values indicate degradation
                    is_degrading = change_percent < -10

                trends[param] = {
                    "first_value": first_value,
                    "last_value": last_value,
                    "change_percent": round(change_percent, 2),
                    "is_degrading": is_degrading,
                }

                if is_degrading:
                    severity = "critical" if change_percent < -20 else "high"
                    degradation_alerts.append(
                        {
                            "parameter": param,
                            "severity": severity,
                            "first_value": first_value,
                            "last_value": last_value,
                            "change_percent": round(change_percent, 2),
                            "message": f"{param.replace('_', ' ').title()} has declined by {abs(change_percent):.1f}% over {months_lookback} months",
                        }
                    )

        # Overall assessment
        degradation_count = len(degradation_alerts)
        if degradation_count >= 3:
            overall_status = "critical"
        elif degradation_count >= 1:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        logger.info(
            f"Degradation analysis complete: {degradation_count} alerts, status: {overall_status}"
        )

        return {
            "status": overall_status,
            "tests_analyzed": len(tests),
            "period_days": (last_test.test_date - first_test.test_date).days,
            "degradation_alerts": degradation_alerts,
            "trends": trends,
            "first_test_date": first_test.test_date,
            "last_test_date": last_test.test_date,
        }

    async def predict_future_soil_health(
        self,
        db: AsyncSession,
        farm_id: int,
        plot_id: Optional[int] = None,
        months_ahead: int = 6,
        user=None,
    ) -> Dict[str, Any]:
        """
        Predict future soil health using linear regression on historical data

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID
            months_ahead: Number of months to predict ahead

        Returns:
            Predictions for key soil parameters
        """
        logger.info(f"Predicting future soil health for farm {farm_id}")

        # Get all historical tests
        tests = _load_soil_tests(farm_id, plot_id, newest_first=False, user=user)

        if len(tests) < 3:
            return {
                "status": "insufficient_data",
                "message": "Need at least 3 soil tests for prediction",
                "tests_found": len(tests),
            }

        # Simple linear regression for each parameter
        predictions = {}
        base_date = tests[0].test_date

        for param in [
            "nitrogen_kg_per_ha",
            "phosphorus_kg_per_ha",
            "potassium_kg_per_ha",
            "ph_level",
            "organic_carbon_percent",
            "soil_health_score",
        ]:
            # Extract data points
            x_values = []  # Days since first test
            y_values = []  # Parameter values

            for test in tests:
                value = getattr(test, param)
                if value is not None:
                    days_since_start = (test.test_date - base_date).days
                    x_values.append(days_since_start)
                    y_values.append(float(value))

            if len(x_values) >= 3:
                # Calculate linear regression: y = mx + b
                n = len(x_values)
                sum_x = sum(x_values)
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_values, y_values))
                sum_x2 = sum(x * x for x in x_values)

                # Slope (m) and intercept (b)
                m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                b = (sum_y - m * sum_x) / n

                # Predict future value
                future_days = (date.today() - base_date).days + (months_ahead * 30)
                predicted_value = m * future_days + b

                # Calculate confidence based on R-squared
                y_mean = sum_y / n
                ss_tot = sum((y - y_mean) ** 2 for y in y_values)
                ss_res = sum((y - (m * x + b)) ** 2 for x, y in zip(x_values, y_values))
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                predictions[param] = {
                    "current_value": y_values[-1],
                    "predicted_value": round(predicted_value, 2),
                    "trend": "increasing" if m > 0 else "decreasing",
                    "confidence": round(r_squared, 2),
                    "data_points": len(x_values),
                }

        logger.info(f"Generated predictions for {len(predictions)} parameters")

        return {
            "status": "success",
            "prediction_date": date.today() + timedelta(days=months_ahead * 30),
            "months_ahead": months_ahead,
            "predictions": predictions,
            "tests_analyzed": len(tests),
        }

    async def generate_improvement_action_plan(
        self,
        db: AsyncSession,
        farm_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Generate prioritized action plan for soil improvement

        Analyzes deficiency patterns across multiple tests and creates
        a comprehensive improvement plan with timeline

        Args:
            db: Database session
            farm_id: Farm ID
            plot_id: Optional plot ID

        Returns:
            Prioritized action plan with timeline
        """
        logger.info(f"Generating improvement action plan for farm {farm_id}")

        # Get latest test (callers may pass only plot_id; resolve its farm)
        if farm_id is None and plot_id:
            farm_id = plot_for_user(plot_id, user)["farm_id"]
        tests = (
            _load_soil_tests(farm_id, plot_id, newest_first=True, limit=1, user=user)
            if farm_id
            else []
        )
        latest_test = tests[0] if tests else None

        if not latest_test:
            return {"status": "no_data", "message": "No soil test data available"}

        # Convert to dict
        soil_data = {
            "nitrogen_kg_per_ha": latest_test.nitrogen_kg_per_ha,
            "phosphorus_kg_per_ha": latest_test.phosphorus_kg_per_ha,
            "potassium_kg_per_ha": latest_test.potassium_kg_per_ha,
            "ph_level": latest_test.ph_level,
            "organic_carbon_percent": latest_test.organic_carbon_percent,
            "electrical_conductivity": latest_test.electrical_conductivity,
            "zinc_ppm": latest_test.zinc_ppm,
            "iron_ppm": latest_test.iron_ppm,
            "manganese_ppm": latest_test.manganese_ppm,
            "copper_ppm": latest_test.copper_ppm,
            "boron_ppm": latest_test.boron_ppm,
        }

        soil_health_score = latest_test.soil_health_score or self.calculate_soil_health_score(
            soil_data
        )

        # Generate recommendations
        recommendations = self.generate_soil_improvement_recommendations(
            soil_data, soil_health_score
        )

        # Organize into action plan with timeline
        immediate_actions = []  # 0-1 month
        short_term_actions = []  # 1-3 months
        medium_term_actions = []  # 3-6 months
        long_term_actions = []  # 6-12 months

        for rec in recommendations:
            timeline = rec.get("timeline", "")

            if "season" in timeline.lower() or "1-3" in timeline:
                short_term_actions.append(rec)
            elif "3-6" in timeline:
                medium_term_actions.append(rec)
            elif "6-12" in timeline or "year" in timeline.lower():
                long_term_actions.append(rec)
            else:
                immediate_actions.append(rec)

        action_plan = {
            "status": "success",
            "test_date": latest_test.test_date,
            "current_soil_health_score": soil_health_score,
            "target_soil_health_score": min(soil_health_score + 15, 100),
            "immediate_actions": immediate_actions,
            "short_term_actions": short_term_actions,
            "medium_term_actions": medium_term_actions,
            "long_term_actions": long_term_actions,
            "total_actions": len(recommendations),
        }

        logger.info(f"Generated action plan with {len(recommendations)} actions")
        return action_plan


# Singleton instance
soil_testing_service = SoilTestingService()
