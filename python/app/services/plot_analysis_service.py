"""
Smart Land Plot Analysis Service
Provides AI-powered crop recommendations based on detailed plot characteristics

Task 26.1: Comprehensive plot analysis with Bedrock AI integration
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional

from app.services.farm_access import Row, fetch_one, plot_for_user

# Rows are farm_access.Row (dict with attribute access); aliases keep the type hints readable.
FarmPlot = Row
SoilTestResult = Row
from app.core.cache import TTL_BEDROCK_API, get_cache_manager
from app.services.bedrock_service import bedrock_service

logger = logging.getLogger(__name__)


def _parse_previous_crops(value) -> List[Dict[str, Any]]:
    """farm_plots.previous_crops is varchar: JSON list of {crop_name} or a comma-separated list."""
    if not value:
        return []
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        data = [c.strip() for c in str(value).split(",") if c.strip()]
    if not isinstance(data, list):
        data = [data]
    return [c if isinstance(c, dict) else {"crop_name": str(c)} for c in data]


class PlotAnalysisService:
    """Service for comprehensive plot analysis with Bedrock AI"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_manager = get_cache_manager()

    async def analyze_plot(
        self,
        plot_id: int,
        season: str,
        budget_per_acre: Optional[float] = None,
        preferences: Optional[Dict[str, str]] = None,
        user=None,
    ) -> Dict[str, Any]:
        """
        Comprehensive plot analysis using Bedrock AI

        Args:
            plot_id: Plot ID to analyze
            season: Target season (kharif/rabi/zaid)
            budget_per_acre: Farmer's investment capacity (optional)
            preferences: Risk tolerance, market focus, organic preference (optional)

        Returns:
            Detailed analysis with ranked crop recommendations and profitability metrics
        """

        # Owner check before the cache, so a cached result is never served to another user.
        if user is not None:
            try:
                plot_for_user(plot_id, user)
            except LookupError as e:
                raise ValueError(str(e))  # router maps ValueError -> 404

        # Check cache first
        if self.cache_manager and self.cache_manager.enabled:
            cache_key = self.cache_manager._generate_cache_key(
                "plot_analysis",
                plot_id=plot_id,
                season=season,
                budget_per_acre=budget_per_acre or 0,
                preferences=json.dumps(preferences or {}),
            )

            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for plot analysis: plot_id={plot_id}, season={season}")
                return cached_result

        # Get plot details
        plot = await self._get_plot_details(plot_id)
        if not plot:
            raise ValueError(f"Plot {plot_id} not found")

        # Get latest soil test results
        soil_data = await self._get_latest_soil_test(plot_id)

        # Build comprehensive plot profile
        plot_profile = self._build_plot_profile(plot, soil_data)

        # Call Bedrock AI for analysis
        analysis = await self._analyze_with_bedrock(
            plot_profile=plot_profile,
            season=season,
            budget_per_acre=budget_per_acre or 20000,  # Default budget
            preferences=preferences or {},
        )

        # Enhance with profitability calculations
        for crop in analysis.get("recommended_crops", []):
            crop["profitability"] = await self._calculate_profitability(
                crop=crop, area=float(plot.area), budget_per_acre=budget_per_acre or 20000
            )

        # Add plot metadata
        result = {
            "plot_id": plot_id,
            "plot_name": plot.plot_name,
            "analysis_date": datetime.now().isoformat(),
            "season": season,
            "plot_characteristics": plot_profile,
            **analysis,
        }

        # Cache the result
        if self.cache_manager and self.cache_manager.enabled:
            self.cache_manager.set(cache_key, result, TTL_BEDROCK_API)
            logger.info(f"Cached plot analysis for plot_id={plot_id} (6-hour TTL)")

        logger.info(f"Plot analysis completed for plot_id={plot_id}, season={season}")
        return result

    async def _get_plot_details(self, plot_id: int) -> Optional[FarmPlot]:
        """Get plot details from database"""
        return fetch_one("SELECT * FROM farm_plots WHERE id = ?", [plot_id])

    async def _get_latest_soil_test(self, plot_id: int) -> Optional[SoilTestResult]:
        """Get latest soil test results for plot"""
        return fetch_one(
            "SELECT * FROM soil_test_results WHERE plot_id = ? ORDER BY test_date DESC, id DESC LIMIT 1",
            [plot_id],
        )

    def _build_plot_profile(
        self, plot: FarmPlot, soil_data: Optional[SoilTestResult]
    ) -> Dict[str, Any]:
        """Build comprehensive plot profile for Bedrock analysis"""

        profile = {
            "location": {"state": plot.state, "district": plot.district},
            "area_acres": float(plot.area),
            "soil_data": {
                "type": plot.soil_type,
                "ph": float(soil_data.ph_level) if soil_data and soil_data.ph_level else None,
                "nitrogen": (
                    float(soil_data.nitrogen_kg_per_ha)
                    if soil_data and soil_data.nitrogen_kg_per_ha
                    else None
                ),
                "phosphorus": (
                    float(soil_data.phosphorus_kg_per_ha)
                    if soil_data and soil_data.phosphorus_kg_per_ha
                    else None
                ),
                "potassium": (
                    float(soil_data.potassium_kg_per_ha)
                    if soil_data and soil_data.potassium_kg_per_ha
                    else None
                ),
                "organic_matter": (
                    float(soil_data.organic_matter_percent)
                    if soil_data and soil_data.organic_matter_percent
                    else None
                ),
                "texture": (
                    "Medium"
                    if not soil_data
                    else (
                        "Fine"
                        if plot.soil_type == "clay"
                        else "Coarse" if plot.soil_type == "sandy" else "Medium"
                    )
                ),
                "health_score": (
                    float(soil_data.soil_health_score)
                    if soil_data and soil_data.soil_health_score
                    else None
                ),
            },
            "water_data": {
                "source": plot.irrigation_type,
                "availability": (
                    "year-round"
                    if "canal" in (plot.irrigation_type or "").lower()
                    or "borewell" in (plot.irrigation_type or "").lower()
                    else "seasonal"
                ),
                "quality": "good",  # Default, can be enhanced with water test data
            },
            "historical_crops": _parse_previous_crops(plot.previous_crops),
        }

        return profile

    async def _analyze_with_bedrock(
        self,
        plot_profile: Dict[str, Any],
        season: str,
        budget_per_acre: float,
        preferences: Dict[str, str],
    ) -> Dict[str, Any]:
        """Call Bedrock AI for comprehensive plot analysis"""

        # Build enhanced prompt with plot-specific details
        prompt = f"""Analyze this agricultural land plot and provide comprehensive crop recommendations:

PLOT DETAILS:
Location: {plot_profile['location']['state']}, {plot_profile['location']['district']}
Area: {plot_profile['area_acres']} acres

SOIL ANALYSIS:
Type: {plot_profile['soil_data']['type']}
pH: {plot_profile['soil_data']['ph'] or 'Not tested'}
Nitrogen: {plot_profile['soil_data']['nitrogen'] or 'Not tested'} kg/ha
Phosphorus: {plot_profile['soil_data']['phosphorus'] or 'Not tested'} kg/ha
Potassium: {plot_profile['soil_data']['potassium'] or 'Not tested'} kg/ha
Organic Matter: {plot_profile['soil_data']['organic_matter'] or 'Not tested'}%
Texture: {plot_profile['soil_data']['texture']}
Health Score: {plot_profile['soil_data']['health_score'] or 'Not calculated'}/100

WATER RESOURCES:
Source: {plot_profile['water_data']['source']}
Availability: {plot_profile['water_data']['availability']}
Quality: {plot_profile['water_data']['quality']}

HISTORICAL PERFORMANCE:
Previous Crops: {', '.join([c.get('crop_name', 'Unknown') for c in plot_profile['historical_crops']]) if plot_profile['historical_crops'] else 'No history'}

FARMER PREFERENCES:
Season: {season}
Budget per acre: ₹{budget_per_acre}
Risk Tolerance: {preferences.get('risk_tolerance', 'medium')}
Market Focus: {preferences.get('market_focus', 'local')}
Organic Preference: {preferences.get('organic', False)}

Provide detailed recommendations for top 5 crops ranked by overall suitability:

For each crop, include:

1. SUITABILITY ANALYSIS (Score 0-10):
   - Soil compatibility score
   - Water requirement match
   - Climate suitability
   - Overall suitability score

2. PROFITABILITY ANALYSIS:
   - Investment per acre (seeds, fertilizer, labor, irrigation)
   - Expected yield range (min-max quintals per acre)
   - Current market price per quintal
   - Expected revenue per acre
   - Expected profit per acre
   - ROI percentage
   - Breakeven yield

3. CULTIVATION DETAILS:
   - Recommended variety for this location
   - Planting window (specific dates)
   - Harvest window (specific dates)
   - Duration in days
   - Water requirement level (Low/Medium/High)
   - Labor requirement level (Low/Medium/High)

4. QUALITY PREDICTION:
   - Expected quality grade (A/B/C)
   - Quality confidence score (0-1)
   - Factors affecting quality

5. MARKET ANALYSIS:
   - Demand level (High/Medium/Low)
   - Price trend (Rising/Stable/Declining)
   - Export potential (Yes/No)
   - Local market size

6. RISK ASSESSMENT:
   - Major risk factors
   - Risk probability (High/Medium/Low)
   - Mitigation strategies

7. WEATHER GUIDANCE:
   - Seasonal weather pattern
   - Optimal planting timing
   - Harvest timing recommendations
   - Weather alerts

8. SOIL RECOMMENDATIONS:
   - Soil preparation steps
   - Fertilizer recommendations
   - Organic matter additions
   - pH adjustment if needed

9. WATER MANAGEMENT:
   - Irrigation schedule
   - Water conservation techniques
   - Drainage requirements

Also provide:

ANNUAL STRATEGY:
- Best crop for this season
- Recommended crop for next season (crop rotation)
- Total annual profit potential
- Annual ROI

PLOT HEALTH SCORE:
- Soil health score (0-100)
- Water resource score (0-100)
- Overall plot suitability score (0-100)

Format as JSON:
{{
  "recommended_crops": [
    {{
      "rank": 1,
      "crop_name": "crop name",
      "variety": "variety name",
      "suitability_score": 9.2,
      "soil_compatibility": 9.0,
      "water_match": 9.5,
      "climate_suitability": 9.0,
      "investment_per_acre": 18000,
      "expected_yield_per_acre": "22-25 quintals",
      "market_price_per_quintal": 2500,
      "expected_revenue_per_acre": 58750,
      "expected_profit_per_acre": 40750,
      "roi_percentage": 226,
      "breakeven_yield": "7.2 quintals",
      "planting_window": "June 15 - July 15",
      "harvest_window": "October 20 - November 10",
      "duration_days": 120,
      "water_requirement": "High",
      "labor_requirement": "Medium",
      "quality_grade": "A",
      "quality_confidence": 0.87,
      "quality_factors": ["Good soil health", "Adequate water"],
      "demand_level": "High",
      "price_trend": "Stable",
      "export_potential": true,
      "local_market_size": "Large",
      "risk_factors": ["Heavy rainfall during harvest"],
      "risk_probability": "Medium",
      "mitigation_strategies": ["Plan harvest before monsoon withdrawal"],
      "seasonal_weather_pattern": "Monsoon rainfall 700-900mm",
      "planting_timing": "After first good monsoon rains",
      "harvest_timing": "Complete by October",
      "weather_alerts": ["Heavy rainfall possible"],
      "soil_preparation": ["Add organic matter", "Apply lime"],
      "fertilizer_recommendations": ["Nitrogen: 120 kg/ha", "Phosphorus: 60 kg/ha"],
      "irrigation_schedule": "Weekly during dry spells",
      "confidence_score": 0.87
    }}
  ],
  "annual_strategy": {{
    "current_season_crop": "crop name",
    "next_season_crop": "crop name",
    "total_annual_profit": 82000,
    "annual_roi": 273
  }},
  "plot_health": {{
    "soil_health_score": 85,
    "water_resource_score": 90,
    "overall_suitability_score": 87
  }},
  "soil_recommendations": ["recommendation1", "recommendation2"],
  "water_recommendations": ["recommendation1", "recommendation2"]
}}

Provide ONLY the JSON response, no additional text."""

        try:
            response_text = bedrock_service._invoke_claude(prompt, max_tokens=4000, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis = json.loads(json_text)
                return analysis
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return self._create_fallback_analysis(plot_profile, season)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._create_fallback_analysis(plot_profile, season)
        except Exception as e:
            logger.error(f"Plot analysis error: {e}")
            raise

    async def _calculate_profitability(
        self, crop: Dict[str, Any], area: float, budget_per_acre: float
    ) -> Dict[str, Any]:
        """
        Calculate detailed profitability metrics

        Returns comprehensive financial analysis including investment breakdown,
        revenue projections, profit calculations, and ROI metrics.
        """

        # Parse yield range (e.g., "22-25 quintals" -> 23.5 average)
        yield_str = crop.get("expected_yield_per_acre", "20 quintals")
        avg_yield = self._parse_yield_range(yield_str)

        # Get values from crop data
        investment_per_acre = Decimal(str(crop.get("investment_per_acre", 15000)))
        market_price = Decimal(str(crop.get("market_price_per_quintal", 2000)))

        # Calculate per acre metrics
        revenue_per_acre = Decimal(str(avg_yield)) * market_price
        profit_per_acre = revenue_per_acre - investment_per_acre
        roi_percentage = (
            (profit_per_acre / investment_per_acre) * 100 if investment_per_acre > 0 else 0
        )
        profit_margin = (profit_per_acre / revenue_per_acre) * 100 if revenue_per_acre > 0 else 0
        breakeven_yield = investment_per_acre / market_price if market_price > 0 else 0

        # Calculate total metrics for entire plot
        total_investment = investment_per_acre * Decimal(str(area))
        total_yield = Decimal(str(avg_yield)) * Decimal(str(area))
        total_revenue = revenue_per_acre * Decimal(str(area))
        total_profit = profit_per_acre * Decimal(str(area))

        return {
            "per_acre": {
                "investment": float(investment_per_acre),
                "expected_yield": yield_str,
                "average_yield": float(avg_yield),
                "market_price": float(market_price),
                "revenue": float(revenue_per_acre),
                "profit": float(profit_per_acre),
                "roi_percentage": float(roi_percentage),
                "profit_margin": float(profit_margin),
                "breakeven_yield": f"{float(breakeven_yield):.1f} quintals",
            },
            "total_plot": {
                "area_acres": area,
                "total_investment": float(total_investment),
                "total_yield": f"{float(total_yield):.1f} quintals",
                "total_revenue": float(total_revenue),
                "total_profit": float(total_profit),
                "roi_percentage": float(roi_percentage),
            },
            "investment_breakdown": {
                "seeds": float(investment_per_acre * Decimal("0.15")),
                "fertilizer": float(investment_per_acre * Decimal("0.35")),
                "labor": float(investment_per_acre * Decimal("0.30")),
                "irrigation": float(investment_per_acre * Decimal("0.15")),
                "other": float(investment_per_acre * Decimal("0.05")),
            },
        }

    def _parse_yield_range(self, yield_str: str) -> float:
        """Parse yield range string to average value"""
        try:
            # Remove "quintals" and other text
            yield_str = yield_str.lower().replace("quintals", "").replace("quintal", "").strip()

            # Check for range (e.g., "22-25")
            if "-" in yield_str:
                parts = yield_str.split("-")
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return (min_val + max_val) / 2
            else:
                # Single value
                return float(yield_str)
        except:
            return 20.0  # Default fallback

    def _create_fallback_analysis(
        self, plot_profile: Dict[str, Any], season: str
    ) -> Dict[str, Any]:
        """Create basic fallback analysis when Bedrock fails"""

        soil_type = plot_profile["soil_data"]["type"].lower()

        # Simple crop selection based on soil type and season
        if season.lower() == "kharif":
            crop = "Rice" if soil_type in ["clay", "loamy"] else "Cotton"
            yield_range = "20-25 quintals"
            investment = 18000
        elif season.lower() == "rabi":
            crop = "Wheat"
            yield_range = "18-22 quintals"
            investment = 15000
        else:
            crop = "Vegetables"
            yield_range = "15-20 quintals"
            investment = 12000

        return {
            "recommended_crops": [
                {
                    "rank": 1,
                    "crop_name": crop,
                    "variety": "Local variety",
                    "suitability_score": 7.0,
                    "investment_per_acre": investment,
                    "expected_yield_per_acre": yield_range,
                    "market_price_per_quintal": 2000,
                    "quality_grade": "B",
                    "quality_confidence": 0.6,
                    "confidence_score": 0.6,
                }
            ],
            "annual_strategy": {
                "current_season_crop": crop,
                "next_season_crop": "Wheat" if season.lower() == "kharif" else "Rice",
                "total_annual_profit": 60000,
                "annual_roi": 200,
            },
            "plot_health": {
                "soil_health_score": 70,
                "water_resource_score": 75,
                "overall_suitability_score": 72,
            },
        }
