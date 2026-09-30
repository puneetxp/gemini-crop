"""
Seasonal Trend Analysis Service
Provides analysis of crop trends across Indian agricultural seasons (Kharif, Rabi, Zaid)
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as Session
from typing import Dict, Optional

from app.services.farm_access import Row, fetch_one
from app.services.market_data_service import MarketDataService

SeasonalTrend = Row  # rows are farm_access.Row (dict with attribute access)

logger = logging.getLogger(__name__)


class SeasonalTrendService:
    """Service for analyzing seasonal trends in crop prices and yields"""

    def __init__(self, db: Session):
        """
        Initialize seasonal trend service

        Args:
            db: Database session
        """
        self.db = db
        self.market_service = MarketDataService(db)

    def analyze_seasonal_trends(
        self, crop_type: str, state: str, district: Optional[str] = None, years: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze trends across all seasons (Kharif, Rabi, Zaid)

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            years: Number of years to analyze

        Returns:
            Dictionary with comprehensive seasonal analysis
        """
        try:
            # Use the market data service's analyze_seasonal_trends method
            analysis = self.market_service.analyze_seasonal_trends(
                crop_type=crop_type, state=state, district=district, years=years
            )

            # Enhance with additional insights
            if analysis.get("comparison"):
                analysis["recommendations"] = self._generate_seasonal_recommendations(
                    analysis["seasonal_breakdown"], analysis["comparison"]
                )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing seasonal trends: {e}")
            raise

    def analyze_season_trend(
        self,
        crop_type: str,
        state: str,
        district: Optional[str] = None,
        season: str = "kharif",
        years: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific season

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            season: Season name (kharif, rabi, zaid)
            years: Number of years to analyze

        Returns:
            Dictionary with season-specific analysis
        """
        try:
            # Get full seasonal analysis
            full_analysis = self.market_service.analyze_seasonal_trends(
                crop_type=crop_type, state=state, district=district, years=years
            )

            # Extract specific season data
            seasonal_data = full_analysis.get("seasonal_breakdown", {}).get(season)

            if not seasonal_data or seasonal_data.get("status") != "success":
                return {
                    "error": f"No data available for {season} season",
                    "crop_type": crop_type,
                    "state": state,
                    "district": district,
                    "season": season,
                }

            # Add season-specific recommendations
            seasonal_data["recommendations"] = self._generate_season_recommendations(
                season, seasonal_data
            )

            # Add seasonal context
            seasonal_data["season_info"] = self._get_season_info(season)

            return seasonal_data

        except Exception as e:
            logger.error(f"Error analyzing season trend: {e}")
            raise

    def forecast_seasonal_prices(
        self,
        crop_type: str,
        state: str,
        season: str,
        district: Optional[str] = None,
        forecast_years: int = 2,
    ) -> Dict[str, Any]:
        """
        Forecast future prices for a specific season

        Args:
            crop_type: Type of crop
            state: State name
            season: Season name
            district: District name (optional)
            forecast_years: Number of years to forecast

        Returns:
            Dictionary with price forecasts
        """
        try:
            # Use market service's forecast method
            forecast = self.market_service.forecast_seasonal_prices(
                crop_type=crop_type,
                state=state,
                season=season,
                district=district,
                forecast_years=forecast_years,
            )

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting seasonal prices: {e}")
            raise

    def identify_seasonal_patterns(
        self, crop_type: str, state: str, district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify patterns across seasons

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)

        Returns:
            Dictionary with identified patterns
        """
        try:
            # Use market service's pattern identification
            patterns = self.market_service.identify_seasonal_patterns(
                crop_type=crop_type, state=state, district=district
            )

            return patterns

        except Exception as e:
            logger.error(f"Error identifying seasonal patterns: {e}")
            raise

    def store_seasonal_trend(
        self,
        crop_type: str,
        state: str,
        district: Optional[str],
        season: str,
        trend_data: Dict[str, Any],
    ) -> SeasonalTrend:
        """
        Store seasonal trend analysis in database

        Args:
            crop_type: Type of crop
            state: State name
            district: District name (optional)
            season: Season name
            trend_data: Analysis data to store

        Returns:
            Created SeasonalTrend instance
        """
        try:
            # Extract relevant data from analysis
            price_metrics = trend_data.get("price_metrics", {})
            trend_analysis = trend_data.get("trend_analysis", {})
            year_range = trend_data.get("year_range", {})

            # Create seasonal trend record
            # yield_trend_yoy stays NULL until yield data is available; weather suitability defaults to 0.8
            seasonal_trend = fetch_one(
                """INSERT INTO seasonal_trends
                   (crop_type, state, district, planting_season, price_trend_yoy, yield_trend_yoy,
                    weather_suitability_score, analysis_start_year, analysis_end_year, years_of_data)
                   VALUES (?, ?, ?, ?, ?, NULL, 0.8, ?, ?, ?) RETURNING *""",
                [
                    crop_type,
                    state,
                    district,
                    season,
                    float(price_metrics.get("cagr", 0) or 0),
                    year_range.get("start"),
                    year_range.get("end"),
                    trend_data.get("data_points", 0),
                ],
            )

            logger.info(f"Stored seasonal trend: {crop_type} - {state} - {season}")
            return seasonal_trend

        except Exception as e:
            logger.error(f"Error storing seasonal trend: {e}")
            raise

    def _generate_seasonal_recommendations(
        self, seasonal_breakdown: Dict[str, Any], comparison: Dict[str, Any]
    ) -> list:
        """
        Generate recommendations based on seasonal analysis

        Args:
            seasonal_breakdown: Seasonal data breakdown
            comparison: Season comparison data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Best season recommendation
        if comparison.get("best_price_growth"):
            best = comparison["best_price_growth"]
            recommendations.append(
                f"Plant in {best['season'].capitalize()} season for best price growth "
                f"({best['cagr']:.1f}% CAGR)"
            )

        # Stability recommendation
        if comparison.get("most_stable"):
            stable = comparison["most_stable"]
            recommendations.append(
                f"{stable['season'].capitalize()} season offers most stable prices "
                f"({stable['volatility']:.1f}% volatility)"
            )

        # Risk warnings
        for season, data in seasonal_breakdown.items():
            if data.get("status") == "success":
                volatility = data["price_metrics"].get("volatility_coefficient", 0)
                if volatility > 20:
                    recommendations.append(
                        f"High price volatility in {season.capitalize()} season - "
                        f"consider advance contracts"
                    )

        return recommendations

    def _generate_season_recommendations(self, season: str, season_data: Dict[str, Any]) -> list:
        """
        Generate recommendations for a specific season

        Args:
            season: Season name
            season_data: Season analysis data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        price_metrics = season_data.get("price_metrics", {})
        trend_analysis = season_data.get("trend_analysis", {})

        # Price trend recommendation
        cagr = price_metrics.get("cagr", 0)
        if cagr > 5:
            recommendations.append(
                f"Strong price growth ({cagr:.1f}% annually) makes {season.capitalize()} "
                f"season attractive for this crop"
            )
        elif cagr < -5:
            recommendations.append(
                f"Declining prices ({cagr:.1f}% annually) in {season.capitalize()} season - "
                f"consider alternative crops"
            )

        # Volatility recommendation
        volatility = price_metrics.get("volatility_coefficient", 0)
        if volatility < 10:
            recommendations.append(
                f"Stable prices in {season.capitalize()} season provide predictable returns"
            )
        elif volatility > 20:
            recommendations.append(
                f"High volatility in {season.capitalize()} season - use risk management strategies"
            )

        # Demand recommendation
        avg_demand = trend_analysis.get("avg_demand_score")
        if avg_demand and avg_demand > 0.7:
            recommendations.append(f"Strong market demand in {season.capitalize()} season")

        return recommendations

    def _get_season_info(self, season: str) -> Dict[str, Any]:
        """
        Get information about a specific season

        Args:
            season: Season name

        Returns:
            Dictionary with season information
        """
        season_info = {
            "kharif": {
                "name": "Kharif (Monsoon Season)",
                "planting_months": "June - July",
                "harvest_months": "September - November",
                "characteristics": "Monsoon-dependent crops",
                "common_crops": ["Rice", "Cotton", "Soybean", "Maize", "Sugarcane"],
                "key_factor": "Rainfall patterns",
            },
            "rabi": {
                "name": "Rabi (Winter Season)",
                "planting_months": "October - November",
                "harvest_months": "March - May",
                "characteristics": "Winter crops requiring cooler temperatures",
                "common_crops": ["Wheat", "Barley", "Mustard", "Chickpea", "Lentils"],
                "key_factor": "Irrigation availability",
            },
            "zaid": {
                "name": "Zaid (Summer Season)",
                "planting_months": "March - April",
                "harvest_months": "June - July",
                "characteristics": "Short-duration summer crops",
                "common_crops": ["Watermelon", "Cucumber", "Fodder crops"],
                "key_factor": "Water availability",
            },
        }

        return season_info.get(season.lower(), {})


def get_seasonal_trend_service(db: Session) -> SeasonalTrendService:
    """
    Factory function to create SeasonalTrendService instance

    Args:
        db: Database session

    Returns:
        SeasonalTrendService instance
    """
    return SeasonalTrendService(db)
