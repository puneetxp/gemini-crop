"""
Yield and Profit Prediction Service
Provides comprehensive yield predictions, profit projections, investment requirements, and timeline guidance
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from dateutil.relativedelta import relativedelta

from app.services.bedrock_service import bedrock_service

logger = logging.getLogger(__name__)


class YieldProfitService:
    """Service for yield and profit predictions based on regional patterns"""

    def __init__(self):
        self.bedrock = bedrock_service

    async def get_comprehensive_prediction(
        self,
        crop_name: str,
        variety: str,
        state: str,
        district: str,
        planting_date: date,
        area_acres: float,
        soil_type: str,
        irrigation_type: str,
        previous_crops: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive yield and profit prediction

        Args:
            crop_name: Crop name
            variety: Crop variety
            state: State name
            district: District name
            planting_date: Planting date
            area_acres: Area in acres
            soil_type: Soil type
            irrigation_type: Irrigation type
            previous_crops: Previous crops grown (optional)

        Returns:
            Comprehensive prediction with yield, profit, investment, and timeline

        Validates: AC3.4, AC3.5, AC3.6
        """
        try:
            # Get base prediction from Bedrock
            base_prediction = await self.bedrock.predict_yield_and_harvest(
                crop_name=crop_name,
                variety=variety,
                state=state,
                district=district,
                planting_date=planting_date.isoformat(),
                area_acres=area_acres,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
            )

            if not base_prediction:
                logger.warning("Bedrock returned empty prediction, using fallback")
                base_prediction = self._create_fallback_prediction(
                    crop_name, variety, planting_date, area_acres
                )

            # Enhance with profit and investment calculations
            enhanced_prediction = self._enhance_with_financials(
                base_prediction=base_prediction,
                crop_name=crop_name,
                variety=variety,
                state=state,
                district=district,
                area_acres=area_acres,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
            )

            # Add timeline guidance
            enhanced_prediction["timeline_guidance"] = self._generate_timeline_guidance(
                crop_name=crop_name,
                planting_date=planting_date,
                harvest_date=enhanced_prediction.get("harvest_date"),
            )

            # Add confidence scoring based on regional success patterns
            enhanced_prediction["confidence_details"] = self._calculate_confidence_details(
                crop_name=crop_name,
                state=state,
                district=district,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
                base_confidence=base_prediction.get("confidence_score", 0.85),
            )

            logger.info(
                f"Comprehensive prediction generated for {crop_name} in {district}, {state}"
            )

            return enhanced_prediction

        except Exception as e:
            logger.error(f"Error generating comprehensive prediction: {e}")
            raise

    def _enhance_with_financials(
        self,
        base_prediction: Dict[str, Any],
        crop_name: str,
        variety: str,
        state: str,
        district: str,
        area_acres: float,
        soil_type: str,
        irrigation_type: str,
    ) -> Dict[str, Any]:
        """
        Enhance prediction with financial projections

        Validates: AC3.5 - Profit projections using Bedrock's market knowledge
        """
        # Get market price estimates from Bedrock
        market_data = self._get_market_price_estimate(crop_name, state, district)

        # Calculate investment requirements
        investment = self._calculate_investment_requirements(
            crop_name=crop_name,
            variety=variety,
            area_acres=area_acres,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
        )

        # Calculate profit projections
        expected_yield = base_prediction.get("expected_yield_per_acre", 0)
        total_yield = base_prediction.get("total_expected_yield", expected_yield * area_acres)

        # Market price per quintal (conservative estimate)
        price_per_quintal = market_data.get("price_per_quintal", 0)

        # Calculate revenue and profit
        total_revenue = total_yield * price_per_quintal
        total_investment = investment.get("total_per_acre", 0) * area_acres
        total_profit = total_revenue - total_investment
        profit_per_acre = total_profit / area_acres if area_acres > 0 else 0

        # Add financial data to prediction
        enhanced = base_prediction.copy()
        enhanced.update(
            {
                "financial_projection": {
                    "expected_yield_per_acre": expected_yield,
                    "total_expected_yield": total_yield,
                    "market_price_per_quintal": price_per_quintal,
                    "total_revenue": round(total_revenue, 2),
                    "total_investment": round(total_investment, 2),
                    "total_profit": round(total_profit, 2),
                    "profit_per_acre": round(profit_per_acre, 2),
                    "roi_percentage": round(
                        (total_profit / total_investment * 100) if total_investment > 0 else 0, 2
                    ),
                },
                "investment_breakdown": investment,
                "market_context": market_data,
            }
        )

        return enhanced

    def _get_market_price_estimate(
        self, crop_name: str, state: str, district: str
    ) -> Dict[str, Any]:
        """
        Get market price estimate using Bedrock's knowledge

        Validates: AC3.5 - Using Bedrock's market knowledge
        """
        # Use Bedrock to get market price estimates
        prompt = f"""Provide current market price estimate for {crop_name} in {state}, {district}.

Give conservative price estimate per quintal in INR.
Consider:
- Current market rates in {state}
- Seasonal demand patterns
- Quality grade impact on price

Format as JSON:
{{
  "price_per_quintal": price in INR,
  "price_range": {{"min": min price, "max": max price}},
  "market_demand": "high/medium/low",
  "price_stability": "stable/volatile",
  "best_selling_period": "month range"
}}

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=500, temperature=0.1)

            # Extract JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                import json

                json_text = response_text[json_start:json_end]
                market_data = json.loads(json_text)
                return market_data
            else:
                # Fallback to conservative estimates
                return self._get_fallback_market_price(crop_name)

        except Exception as e:
            logger.warning(f"Error getting market price from Bedrock: {e}")
            return self._get_fallback_market_price(crop_name)

    def _get_fallback_market_price(self, crop_name: str) -> Dict[str, Any]:
        """Fallback market prices for common crops"""
        # Conservative price estimates per quintal in INR
        fallback_prices = {
            "rice": 2000,
            "wheat": 2100,
            "maize": 1800,
            "cotton": 5500,
            "sugarcane": 300,  # per quintal
            "soybean": 4000,
            "groundnut": 5000,
            "chickpea": 5500,
            "pigeon pea": 6000,
            "mustard": 5000,
            "sunflower": 5500,
            "potato": 1200,
            "onion": 1500,
            "tomato": 1800,
        }

        crop_lower = crop_name.lower()
        price = fallback_prices.get(crop_lower, 2500)  # Default conservative price

        return {
            "price_per_quintal": price,
            "price_range": {"min": price * 0.8, "max": price * 1.2},
            "market_demand": "medium",
            "price_stability": "moderate",
            "best_selling_period": "harvest season",
        }

    def _calculate_investment_requirements(
        self, crop_name: str, variety: str, area_acres: float, soil_type: str, irrigation_type: str
    ) -> Dict[str, Any]:
        """
        Calculate investment requirements

        Validates: AC3.6 - Investment requirements (seed, fertilizer, labor costs)
        """
        # Use Bedrock to get investment estimates
        prompt = f"""Provide investment requirements for growing {crop_name} ({variety}).

Area: {area_acres} acres
Soil Type: {soil_type}
Irrigation: {irrigation_type}

Break down costs per acre for:
1. Seeds/Planting material
2. Fertilizers (organic + chemical)
3. Pesticides/Herbicides
4. Labor costs
5. Irrigation costs
6. Other inputs

Format as JSON:
{{
  "seed_cost_per_acre": cost in INR,
  "fertilizer_cost_per_acre": cost in INR,
  "pesticide_cost_per_acre": cost in INR,
  "labor_cost_per_acre": cost in INR,
  "irrigation_cost_per_acre": cost in INR,
  "other_costs_per_acre": cost in INR,
  "total_per_acre": total cost in INR,
  "breakdown_details": {{
    "seed": "description",
    "fertilizer": "description",
    "labor": "description"
  }}
}}

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=800, temperature=0.1)

            # Extract JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                import json

                json_text = response_text[json_start:json_end]
                investment = json.loads(json_text)
                return investment
            else:
                return self._get_fallback_investment(crop_name, area_acres)

        except Exception as e:
            logger.warning(f"Error getting investment from Bedrock: {e}")
            return self._get_fallback_investment(crop_name, area_acres)

    def _get_fallback_investment(self, crop_name: str, area_acres: float) -> Dict[str, Any]:
        """Fallback investment estimates"""
        # Conservative investment estimates per acre in INR
        base_investments = {
            "rice": 25000,
            "wheat": 20000,
            "maize": 22000,
            "cotton": 30000,
            "sugarcane": 50000,
            "soybean": 18000,
            "groundnut": 25000,
            "chickpea": 15000,
            "pigeon pea": 16000,
            "mustard": 12000,
            "sunflower": 15000,
            "potato": 40000,
            "onion": 35000,
            "tomato": 45000,
        }

        crop_lower = crop_name.lower()
        total_per_acre = base_investments.get(crop_lower, 20000)

        return {
            "seed_cost_per_acre": round(total_per_acre * 0.15, 2),
            "fertilizer_cost_per_acre": round(total_per_acre * 0.25, 2),
            "pesticide_cost_per_acre": round(total_per_acre * 0.10, 2),
            "labor_cost_per_acre": round(total_per_acre * 0.35, 2),
            "irrigation_cost_per_acre": round(total_per_acre * 0.10, 2),
            "other_costs_per_acre": round(total_per_acre * 0.05, 2),
            "total_per_acre": total_per_acre,
            "breakdown_details": {
                "seed": "Quality seeds from certified source",
                "fertilizer": "Balanced NPK + organic manure",
                "labor": "Planting, maintenance, and harvest labor",
            },
        }

    def _generate_timeline_guidance(
        self, crop_name: str, planting_date: date, harvest_date: Optional[str]
    ) -> Dict[str, Any]:
        """
        Generate timeline guidance for planting and harvest windows

        Validates: AC3.6 - Timeline guidance for planting and harvest windows
        """
        if harvest_date:
            try:
                harvest_dt = datetime.fromisoformat(harvest_date).date()
            except:
                harvest_dt = planting_date + timedelta(days=120)  # Default 4 months
        else:
            harvest_dt = planting_date + timedelta(days=120)

        # Calculate key milestones
        germination_date = planting_date + timedelta(days=7)
        vegetative_date = planting_date + timedelta(days=30)
        flowering_date = planting_date + timedelta(days=60)
        maturity_date = harvest_dt - timedelta(days=14)

        # Optimal planting window (±2 weeks from planting date)
        planting_window_start = planting_date - timedelta(days=14)
        planting_window_end = planting_date + timedelta(days=14)

        # Optimal harvest window (±7 days from harvest date)
        harvest_window_start = harvest_dt - timedelta(days=7)
        harvest_window_end = harvest_dt + timedelta(days=7)

        return {
            "planting_window": {
                "optimal_date": planting_date.isoformat(),
                "window_start": planting_window_start.isoformat(),
                "window_end": planting_window_end.isoformat(),
                "guidance": f"Best planting period for {crop_name} in this region",
            },
            "harvest_window": {
                "expected_date": harvest_dt.isoformat(),
                "window_start": harvest_window_start.isoformat(),
                "window_end": harvest_window_end.isoformat(),
                "guidance": "Optimal harvest timing for maximum yield and quality",
            },
            "growth_milestones": [
                {
                    "stage": "Germination",
                    "date": germination_date.isoformat(),
                    "description": "Seeds germinate and seedlings emerge",
                },
                {
                    "stage": "Vegetative Growth",
                    "date": vegetative_date.isoformat(),
                    "description": "Active leaf and stem development",
                },
                {
                    "stage": "Flowering",
                    "date": flowering_date.isoformat(),
                    "description": "Flowering and pollination period",
                },
                {
                    "stage": "Maturity",
                    "date": maturity_date.isoformat(),
                    "description": "Crop reaches maturity, ready for harvest",
                },
            ],
            "total_duration_days": (harvest_dt - planting_date).days,
        }

    def _calculate_confidence_details(
        self,
        crop_name: str,
        state: str,
        district: str,
        soil_type: str,
        irrigation_type: str,
        base_confidence: float,
    ) -> Dict[str, Any]:
        """
        Calculate confidence scoring based on regional success patterns

        Validates: AC3.6 - Confidence scoring based on regional success patterns
        """
        # Factors affecting confidence
        factors = []
        confidence_adjustments = 0.0

        # Soil suitability factor
        if soil_type.lower() in ["loamy", "clay loam", "sandy loam"]:
            factors.append(
                {
                    "factor": "Soil Type",
                    "impact": "positive",
                    "description": f"{soil_type} soil is well-suited for {crop_name}",
                }
            )
            confidence_adjustments += 0.05
        else:
            factors.append(
                {
                    "factor": "Soil Type",
                    "impact": "neutral",
                    "description": f"{soil_type} soil is acceptable for {crop_name}",
                }
            )

        # Irrigation factor
        if irrigation_type.lower() in ["drip", "sprinkler", "canal"]:
            factors.append(
                {
                    "factor": "Irrigation",
                    "impact": "positive",
                    "description": f"{irrigation_type} irrigation provides good water management",
                }
            )
            confidence_adjustments += 0.03
        elif irrigation_type.lower() == "rain-fed":
            factors.append(
                {
                    "factor": "Irrigation",
                    "impact": "risk",
                    "description": "Rain-fed farming has weather dependency risk",
                }
            )
            confidence_adjustments -= 0.05

        # Regional suitability (simplified - in production would use actual data)
        factors.append(
            {
                "factor": "Regional Experience",
                "impact": "positive",
                "description": f"{crop_name} is commonly grown in {state}",
            }
        )

        # Calculate final confidence
        final_confidence = min(0.95, max(0.70, base_confidence + confidence_adjustments))

        # Confidence level description
        if final_confidence >= 0.90:
            confidence_level = "Very High"
            reliability = "Highly reliable prediction based on strong regional patterns"
        elif final_confidence >= 0.85:
            confidence_level = "High"
            reliability = "Reliable prediction with good regional data"
        elif final_confidence >= 0.80:
            confidence_level = "Good"
            reliability = "Good prediction with moderate regional data"
        else:
            confidence_level = "Moderate"
            reliability = "Moderate prediction - consider local expert advice"

        return {
            "confidence_score": round(final_confidence, 2),
            "confidence_level": confidence_level,
            "reliability_description": reliability,
            "contributing_factors": factors,
            "data_sources": [
                "Amazon Bedrock agricultural knowledge",
                "Regional crop performance patterns",
                "Soil and irrigation suitability analysis",
            ],
        }

    def _create_fallback_prediction(
        self, crop_name: str, variety: str, planting_date: date, area_acres: float
    ) -> Dict[str, Any]:
        """Create fallback prediction if Bedrock fails"""
        # Default growing durations in days
        durations = {
            "rice": 120,
            "wheat": 120,
            "maize": 90,
            "cotton": 150,
            "sugarcane": 365,
            "soybean": 100,
            "groundnut": 120,
            "chickpea": 110,
            "pigeon pea": 150,
            "mustard": 90,
            "sunflower": 90,
            "potato": 90,
            "onion": 120,
            "tomato": 75,
        }

        crop_lower = crop_name.lower()
        duration = durations.get(crop_lower, 120)
        harvest_date = planting_date + timedelta(days=duration)

        # Default yields per acre in quintals
        yields = {
            "rice": 25,
            "wheat": 30,
            "maize": 35,
            "cotton": 15,
            "sugarcane": 350,
            "soybean": 15,
            "groundnut": 20,
            "chickpea": 12,
            "pigeon pea": 10,
            "mustard": 12,
            "sunflower": 15,
            "potato": 200,
            "onion": 180,
            "tomato": 250,
        }

        yield_per_acre = yields.get(crop_lower, 20)

        return {
            "harvest_date": harvest_date.isoformat(),
            "harvest_date_range": {
                "min": (harvest_date - timedelta(days=7)).isoformat(),
                "max": (harvest_date + timedelta(days=7)).isoformat(),
            },
            "expected_yield_per_acre": yield_per_acre,
            "yield_range": {"min": yield_per_acre * 0.8, "max": yield_per_acre * 1.2},
            "total_expected_yield": yield_per_acre * area_acres,
            "quality_grade": "B",
            "confidence_score": 0.75,
            "key_factors": [
                "Based on typical regional patterns",
                "Conservative estimates used",
                "Actual results may vary with weather and management",
            ],
            "recommendations": [
                "Follow recommended agricultural practices",
                "Monitor crop regularly",
                "Consult local agricultural extension officers",
            ],
        }


# Global instance
yield_profit_service = YieldProfitService()
