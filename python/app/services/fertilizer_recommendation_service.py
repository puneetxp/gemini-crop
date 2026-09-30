"""
Fertilizer Recommendation Engine Service
Handles soil nutrient analysis, fertilizer recommendations (N, P, K optimization),
application timing, organic vs chemical balancing, and cost optimization

Task 24.1: Implement fertilizer recommendation engine
Validates: Requirements AC9 (Phase 6 - Required)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FertilizerRecommendationService:
    """Service for fertilizer recommendations and nutrient management"""

    # Crop nutrient requirements (N, P, K in kg/ha)
    CROP_NUTRIENT_REQUIREMENTS = {
        "rice": {"N": 120, "P": 60, "K": 40, "growth_days": 120},
        "wheat": {"N": 120, "P": 60, "K": 40, "growth_days": 120},
        "maize": {"N": 150, "P": 75, "K": 50, "growth_days": 90},
        "cotton": {"N": 120, "P": 60, "K": 60, "growth_days": 150},
        "sugarcane": {"N": 250, "P": 115, "K": 115, "growth_days": 365},
        "soybean": {"N": 30, "P": 60, "K": 40, "growth_days": 100},  # Legume - fixes nitrogen
        "chickpea": {"N": 20, "P": 40, "K": 20, "growth_days": 120},  # Legume
        "pigeon_pea": {"N": 25, "P": 50, "K": 25, "growth_days": 150},  # Legume
        "groundnut": {"N": 25, "P": 50, "K": 75, "growth_days": 120},  # Legume
        "mustard": {"N": 80, "P": 40, "K": 20, "growth_days": 120},
        "potato": {"N": 150, "P": 75, "K": 150, "growth_days": 90},
        "tomato": {"N": 150, "P": 75, "K": 100, "growth_days": 90},
        "onion": {"N": 100, "P": 50, "K": 100, "growth_days": 120},
        "default": {"N": 100, "P": 50, "K": 50, "growth_days": 120},
    }

    # Fertilizer types and their nutrient content (%)
    FERTILIZER_TYPES = {
        "urea": {"N": 46, "P": 0, "K": 0, "cost_per_kg": 6.0, "type": "chemical"},
        "dap": {
            "N": 18,
            "P": 46,
            "K": 0,
            "cost_per_kg": 27.0,
            "type": "chemical",
        },  # Di-ammonium phosphate
        "mop": {
            "N": 0,
            "P": 0,
            "K": 60,
            "cost_per_kg": 17.0,
            "type": "chemical",
        },  # Muriate of potash
        "ssp": {
            "N": 0,
            "P": 16,
            "K": 0,
            "cost_per_kg": 8.0,
            "type": "chemical",
        },  # Single super phosphate
        "npk_complex": {"N": 12, "P": 32, "K": 16, "cost_per_kg": 22.0, "type": "chemical"},
        "farmyard_manure": {"N": 0.5, "P": 0.25, "K": 0.5, "cost_per_kg": 1.5, "type": "organic"},
        "compost": {"N": 1.5, "P": 1.0, "K": 1.5, "cost_per_kg": 2.0, "type": "organic"},
        "vermicompost": {"N": 2.0, "P": 1.5, "K": 1.5, "cost_per_kg": 4.0, "type": "organic"},
        "neem_cake": {"N": 5.0, "P": 1.0, "K": 1.5, "cost_per_kg": 15.0, "type": "organic"},
    }

    # Growth stages and fertilizer application timing
    GROWTH_STAGES = {
        "basal": {"timing_days": 0, "N_percent": 50, "P_percent": 100, "K_percent": 50},
        "vegetative": {"timing_days": 30, "N_percent": 25, "P_percent": 0, "K_percent": 25},
        "flowering": {"timing_days": 60, "N_percent": 25, "P_percent": 0, "K_percent": 25},
    }

    def __init__(self):
        """Initialize fertilizer recommendation service"""
        pass

    def calculate_nutrient_requirements(
        self,
        crop_type: str,
        area_hectares: float,
        soil_data: Dict[str, Any],
        target_yield_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Calculate N, P, K requirements based on crop needs and soil deficiencies

        Args:
            crop_type: Type of crop to be grown
            area_hectares: Area in hectares
            soil_data: Current soil nutrient levels
            target_yield_factor: Multiplier for target yield (1.0 = normal, 1.2 = 20% higher)

        Returns:
            Dictionary with nutrient requirements
        """
        logger.info(f"Calculating nutrient requirements for {crop_type} on {area_hectares} ha")

        # Get crop requirements
        crop_key = crop_type.lower().replace(" ", "_")
        crop_req = self.CROP_NUTRIENT_REQUIREMENTS.get(
            crop_key, self.CROP_NUTRIENT_REQUIREMENTS["default"]
        )

        # Calculate total crop requirements (adjusted for target yield)
        total_n_required = crop_req["N"] * area_hectares * target_yield_factor
        total_p_required = crop_req["P"] * area_hectares * target_yield_factor
        total_k_required = crop_req["K"] * area_hectares * target_yield_factor

        # Get current soil nutrient levels
        soil_n = soil_data.get("nitrogen_kg_per_ha", 0) * area_hectares
        soil_p = soil_data.get("phosphorus_kg_per_ha", 0) * area_hectares
        soil_k = soil_data.get("potassium_kg_per_ha", 0) * area_hectares

        # Calculate deficiencies (what needs to be added)
        n_deficit = max(0, total_n_required - soil_n)
        p_deficit = max(0, total_p_required - soil_p)
        k_deficit = max(0, total_k_required - soil_k)

        logger.info(
            f"Nutrient deficits - N: {n_deficit:.2f} kg, P: {p_deficit:.2f} kg, K: {k_deficit:.2f} kg"
        )

        return {
            "crop_type": crop_type,
            "area_hectares": area_hectares,
            "target_yield_factor": target_yield_factor,
            "crop_requirements": {
                "N": total_n_required,
                "P": total_p_required,
                "K": total_k_required,
            },
            "soil_available": {"N": soil_n, "P": soil_p, "K": soil_k},
            "deficits": {"N": n_deficit, "P": p_deficit, "K": k_deficit},
            "per_hectare_requirements": {
                "N": n_deficit / area_hectares if area_hectares > 0 else 0,
                "P": p_deficit / area_hectares if area_hectares > 0 else 0,
                "K": k_deficit / area_hectares if area_hectares > 0 else 0,
            },
        }

    def generate_fertilizer_recommendations(
        self,
        nutrient_requirements: Dict[str, Any],
        organic_preference: float = 0.3,
        budget_per_hectare: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate specific fertilizer recommendations with types and quantities

        Args:
            nutrient_requirements: Output from calculate_nutrient_requirements
            organic_preference: Ratio of organic to total (0.0-1.0), default 30%
            budget_per_hectare: Optional budget constraint per hectare

        Returns:
            Fertilizer recommendations with types and quantities
        """
        logger.info("Generating fertilizer recommendations")

        n_deficit = nutrient_requirements["deficits"]["N"]
        p_deficit = nutrient_requirements["deficits"]["P"]
        k_deficit = nutrient_requirements["deficits"]["K"]
        area = nutrient_requirements["area_hectares"]

        # Calculate organic and chemical portions
        organic_n = n_deficit * organic_preference
        chemical_n = n_deficit * (1 - organic_preference)

        organic_p = p_deficit * organic_preference
        chemical_p = p_deficit * (1 - organic_preference)

        organic_k = k_deficit * organic_preference
        chemical_k = k_deficit * (1 - organic_preference)

        recommendations = []
        total_cost = 0.0

        # Organic fertilizers (use vermicompost as primary organic source)
        if organic_preference > 0:
            vermicompost_n_content = self.FERTILIZER_TYPES["vermicompost"]["N"] / 100
            vermicompost_p_content = self.FERTILIZER_TYPES["vermicompost"]["P"] / 100
            vermicompost_k_content = self.FERTILIZER_TYPES["vermicompost"]["K"] / 100

            # Calculate quantity needed based on N requirement (limiting factor)
            vermicompost_kg = (
                organic_n / vermicompost_n_content if vermicompost_n_content > 0 else 0
            )

            # Calculate actual nutrients provided
            actual_organic_n = vermicompost_kg * vermicompost_n_content
            actual_organic_p = vermicompost_kg * vermicompost_p_content
            actual_organic_k = vermicompost_kg * vermicompost_k_content

            vermicompost_cost = (
                vermicompost_kg * self.FERTILIZER_TYPES["vermicompost"]["cost_per_kg"]
            )
            total_cost += vermicompost_cost

            recommendations.append(
                {
                    "fertilizer_type": "vermicompost",
                    "category": "organic",
                    "quantity_kg": round(vermicompost_kg, 2),
                    "quantity_per_hectare": round(vermicompost_kg / area, 2) if area > 0 else 0,
                    "nutrients_provided": {
                        "N": round(actual_organic_n, 2),
                        "P": round(actual_organic_p, 2),
                        "K": round(actual_organic_k, 2),
                    },
                    "cost_total": round(vermicompost_cost, 2),
                    "cost_per_hectare": round(vermicompost_cost / area, 2) if area > 0 else 0,
                    "application_method": "Mix with soil before planting or apply as top dressing",
                    "benefits": "Improves soil structure, water retention, and microbial activity",
                }
            )

            # Adjust chemical requirements based on what organic provided
            chemical_n = max(0, chemical_n - (actual_organic_n - organic_n))
            chemical_p = max(0, chemical_p - (actual_organic_p - organic_p))
            chemical_k = max(0, chemical_k - (actual_organic_k - organic_k))

        # Chemical fertilizers
        # DAP for phosphorus (also provides some nitrogen)
        if chemical_p > 0:
            dap_p_content = self.FERTILIZER_TYPES["dap"]["P"] / 100
            dap_n_content = self.FERTILIZER_TYPES["dap"]["N"] / 100

            dap_kg = chemical_p / dap_p_content if dap_p_content > 0 else 0
            dap_n_provided = dap_kg * dap_n_content
            dap_cost = dap_kg * self.FERTILIZER_TYPES["dap"]["cost_per_kg"]
            total_cost += dap_cost

            recommendations.append(
                {
                    "fertilizer_type": "dap",
                    "category": "chemical",
                    "quantity_kg": round(dap_kg, 2),
                    "quantity_per_hectare": round(dap_kg / area, 2) if area > 0 else 0,
                    "nutrients_provided": {
                        "N": round(dap_n_provided, 2),
                        "P": round(chemical_p, 2),
                        "K": 0,
                    },
                    "cost_total": round(dap_cost, 2),
                    "cost_per_hectare": round(dap_cost / area, 2) if area > 0 else 0,
                    "application_method": "Apply as basal dose before planting",
                    "benefits": "Quick-release phosphorus for root development",
                }
            )

            # Reduce nitrogen requirement by what DAP provided
            chemical_n = max(0, chemical_n - dap_n_provided)

        # Urea for remaining nitrogen
        if chemical_n > 0:
            urea_n_content = self.FERTILIZER_TYPES["urea"]["N"] / 100
            urea_kg = chemical_n / urea_n_content if urea_n_content > 0 else 0
            urea_cost = urea_kg * self.FERTILIZER_TYPES["urea"]["cost_per_kg"]
            total_cost += urea_cost

            recommendations.append(
                {
                    "fertilizer_type": "urea",
                    "category": "chemical",
                    "quantity_kg": round(urea_kg, 2),
                    "quantity_per_hectare": round(urea_kg / area, 2) if area > 0 else 0,
                    "nutrients_provided": {"N": round(chemical_n, 2), "P": 0, "K": 0},
                    "cost_total": round(urea_cost, 2),
                    "cost_per_hectare": round(urea_cost / area, 2) if area > 0 else 0,
                    "application_method": "Split application: 50% basal, 25% at 30 days, 25% at 60 days",
                    "benefits": "High nitrogen content for vegetative growth",
                }
            )

        # MOP for potassium
        if chemical_k > 0:
            mop_k_content = self.FERTILIZER_TYPES["mop"]["K"] / 100
            mop_kg = chemical_k / mop_k_content if mop_k_content > 0 else 0
            mop_cost = mop_kg * self.FERTILIZER_TYPES["mop"]["cost_per_kg"]
            total_cost += mop_cost

            recommendations.append(
                {
                    "fertilizer_type": "mop",
                    "category": "chemical",
                    "quantity_kg": round(mop_kg, 2),
                    "quantity_per_hectare": round(mop_kg / area, 2) if area > 0 else 0,
                    "nutrients_provided": {"N": 0, "P": 0, "K": round(chemical_k, 2)},
                    "cost_total": round(mop_cost, 2),
                    "cost_per_hectare": round(mop_cost / area, 2) if area > 0 else 0,
                    "application_method": "Split application: 50% basal, 50% at flowering",
                    "benefits": "Improves crop quality and disease resistance",
                }
            )

        # Check budget constraint
        cost_per_hectare = total_cost / area if area > 0 else 0
        within_budget = True
        if budget_per_hectare and cost_per_hectare > budget_per_hectare:
            within_budget = False
            logger.warning(
                f"Fertilizer cost ({cost_per_hectare:.2f}/ha) exceeds budget ({budget_per_hectare:.2f}/ha)"
            )

        logger.info(
            f"Generated {len(recommendations)} fertilizer recommendations, total cost: ₹{total_cost:.2f}"
        )

        return {
            "recommendations": recommendations,
            "total_cost": round(total_cost, 2),
            "cost_per_hectare": round(cost_per_hectare, 2),
            "within_budget": within_budget,
            "budget_per_hectare": budget_per_hectare,
            "organic_ratio": organic_preference,
            "summary": {
                "total_fertilizers": len(recommendations),
                "organic_fertilizers": sum(
                    1 for r in recommendations if r["category"] == "organic"
                ),
                "chemical_fertilizers": sum(
                    1 for r in recommendations if r["category"] == "chemical"
                ),
            },
        }

    def optimize_application_timing(
        self,
        crop_type: str,
        planting_date: date,
        fertilizer_recommendations: List[Dict[str, Any]],
        weather_forecast: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize fertilizer application timing based on crop growth stages and weather

        Args:
            crop_type: Type of crop
            planting_date: Date when crop was planted
            fertilizer_recommendations: List of fertilizer recommendations
            weather_forecast: Optional weather forecast data

        Returns:
            Application schedule with timing and quantities
        """
        logger.info(f"Optimizing application timing for {crop_type}")

        # Get crop growth duration
        crop_key = crop_type.lower().replace(" ", "_")
        crop_data = self.CROP_NUTRIENT_REQUIREMENTS.get(
            crop_key, self.CROP_NUTRIENT_REQUIREMENTS["default"]
        )

        application_schedule = []

        # Group fertilizers by nutrient type
        n_fertilizers = []
        p_fertilizers = []
        k_fertilizers = []
        organic_fertilizers = []

        for fert in fertilizer_recommendations:
            if fert["category"] == "organic":
                organic_fertilizers.append(fert)
            else:
                nutrients = fert["nutrients_provided"]
                if nutrients["N"] > 0:
                    n_fertilizers.append(fert)
                if nutrients["P"] > 0:
                    p_fertilizers.append(fert)
                if nutrients["K"] > 0:
                    k_fertilizers.append(fert)

        # Basal application (at planting)
        basal_date = planting_date
        basal_applications = []

        # All organic fertilizers go as basal
        for fert in organic_fertilizers:
            basal_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"],
                    "quantity_per_hectare": fert["quantity_per_hectare"],
                    "application_method": "Mix with soil before planting",
                }
            )

        # All phosphorus goes as basal (immobile nutrient)
        for fert in p_fertilizers:
            basal_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"],
                    "quantity_per_hectare": fert["quantity_per_hectare"],
                    "application_method": "Apply in furrows or broadcast and incorporate",
                }
            )

        # 50% of potassium as basal
        for fert in k_fertilizers:
            basal_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"] * 0.5,
                    "quantity_per_hectare": fert["quantity_per_hectare"] * 0.5,
                    "application_method": "Apply as basal dose",
                }
            )

        # 50% of nitrogen as basal
        for fert in n_fertilizers:
            basal_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"] * 0.5,
                    "quantity_per_hectare": fert["quantity_per_hectare"] * 0.5,
                    "application_method": "Apply as basal dose",
                }
            )

        if basal_applications:
            application_schedule.append(
                {
                    "stage": "basal",
                    "timing": "At planting",
                    "date": basal_date,
                    "days_after_planting": 0,
                    "applications": basal_applications,
                    "weather_considerations": "Ensure soil has adequate moisture. Avoid application if heavy rain expected within 24 hours.",
                    "precautions": "Mix fertilizers thoroughly with soil. Avoid direct contact with seeds.",
                }
            )

        # First top dressing (30 days after planting - vegetative stage)
        vegetative_date = planting_date + timedelta(days=30)
        vegetative_applications = []

        # 25% of nitrogen
        for fert in n_fertilizers:
            vegetative_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"] * 0.25,
                    "quantity_per_hectare": fert["quantity_per_hectare"] * 0.25,
                    "application_method": "Top dressing near plant rows",
                }
            )

        if vegetative_applications:
            weather_note = self._get_weather_timing_advice(vegetative_date, weather_forecast)
            application_schedule.append(
                {
                    "stage": "vegetative",
                    "timing": "30 days after planting",
                    "date": vegetative_date,
                    "days_after_planting": 30,
                    "applications": vegetative_applications,
                    "weather_considerations": weather_note,
                    "precautions": "Apply when soil is moist. Irrigate if no rain expected. Avoid application during hot afternoon.",
                }
            )

        # Second top dressing (60 days after planting - flowering stage)
        flowering_date = planting_date + timedelta(days=60)
        flowering_applications = []

        # Remaining 25% of nitrogen
        for fert in n_fertilizers:
            flowering_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"] * 0.25,
                    "quantity_per_hectare": fert["quantity_per_hectare"] * 0.25,
                    "application_method": "Top dressing near plant rows",
                }
            )

        # Remaining 50% of potassium
        for fert in k_fertilizers:
            flowering_applications.append(
                {
                    "fertilizer_type": fert["fertilizer_type"],
                    "quantity_kg": fert["quantity_kg"] * 0.5,
                    "quantity_per_hectare": fert["quantity_per_hectare"] * 0.5,
                    "application_method": "Top dressing near plant rows",
                }
            )

        if flowering_applications:
            weather_note = self._get_weather_timing_advice(flowering_date, weather_forecast)
            application_schedule.append(
                {
                    "stage": "flowering",
                    "timing": "60 days after planting",
                    "date": flowering_date,
                    "days_after_planting": 60,
                    "applications": flowering_applications,
                    "weather_considerations": weather_note,
                    "precautions": "Critical stage for yield. Ensure timely application. Combine with irrigation if needed.",
                }
            )

        logger.info(f"Generated {len(application_schedule)} application stages")

        return {
            "crop_type": crop_type,
            "planting_date": planting_date,
            "total_applications": len(application_schedule),
            "schedule": application_schedule,
            "general_guidelines": [
                "Always apply fertilizers when soil has adequate moisture",
                "Avoid application before heavy rain to prevent nutrient loss",
                "Apply nitrogen fertilizers in split doses to reduce leaching",
                "Incorporate fertilizers into soil when possible",
                "Maintain proper spacing from plant stems to avoid burning",
            ],
        }

    def _get_weather_timing_advice(
        self, application_date: date, weather_forecast: Optional[Dict[str, Any]]
    ) -> str:
        """Generate weather-based timing advice"""
        if not weather_forecast:
            return "Check weather forecast. Avoid application if heavy rain expected within 24-48 hours."

        # This would integrate with actual weather forecast data
        # For now, return general advice
        return "Check weather forecast. Avoid application if heavy rain expected within 24-48 hours. Apply when soil is moist but not waterlogged."

    def optimize_for_budget(
        self,
        nutrient_requirements: Dict[str, Any],
        budget_per_hectare: float,
        min_organic_ratio: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generate cost-optimized fertilizer plan within budget constraints

        Args:
            nutrient_requirements: Nutrient requirements from calculate_nutrient_requirements
            budget_per_hectare: Maximum budget per hectare
            min_organic_ratio: Minimum organic fertilizer ratio (default 20%)

        Returns:
            Budget-optimized fertilizer recommendations
        """
        logger.info(f"Optimizing fertilizer plan for budget: ₹{budget_per_hectare}/ha")

        area = nutrient_requirements["area_hectares"]
        total_budget = budget_per_hectare * area

        # Try different organic ratios from minimum to 50%
        best_plan = None
        best_score = 0

        for organic_ratio in [min_organic_ratio, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
            plan = self.generate_fertilizer_recommendations(
                nutrient_requirements,
                organic_preference=organic_ratio,
                budget_per_hectare=budget_per_hectare,
            )

            if plan["within_budget"]:
                # Score based on organic ratio and cost efficiency
                cost_efficiency = 1 - (plan["cost_per_hectare"] / budget_per_hectare)
                score = organic_ratio * 0.6 + cost_efficiency * 0.4

                if score > best_score:
                    best_score = score
                    best_plan = plan

        # If no plan fits budget, create minimal plan
        if not best_plan:
            logger.warning("No plan fits budget, creating minimal plan")
            best_plan = self.generate_fertilizer_recommendations(
                nutrient_requirements,
                organic_preference=min_organic_ratio,
                budget_per_hectare=budget_per_hectare,
            )

            # Scale down quantities to fit budget
            if best_plan["cost_per_hectare"] > budget_per_hectare:
                scale_factor = budget_per_hectare / best_plan["cost_per_hectare"]

                for rec in best_plan["recommendations"]:
                    rec["quantity_kg"] *= scale_factor
                    rec["quantity_per_hectare"] *= scale_factor
                    rec["cost_total"] *= scale_factor
                    rec["cost_per_hectare"] *= scale_factor
                    for nutrient in rec["nutrients_provided"]:
                        rec["nutrients_provided"][nutrient] *= scale_factor

                best_plan["total_cost"] *= scale_factor
                best_plan["cost_per_hectare"] *= scale_factor
                best_plan["within_budget"] = True
                best_plan["note"] = (
                    "Quantities scaled down to fit budget. Consider increasing budget for optimal results."
                )

        logger.info(
            f"Optimized plan: ₹{best_plan['cost_per_hectare']:.2f}/ha, organic ratio: {best_plan['organic_ratio']:.1%}"
        )

        return best_plan

    def balance_organic_chemical(
        self,
        nutrient_requirements: Dict[str, Any],
        soil_health_score: float,
        farmer_preference: str = "balanced",
    ) -> Dict[str, Any]:
        """
        Balance organic vs chemical fertilizers for soil health and cost optimization

        Args:
            nutrient_requirements: Nutrient requirements
            soil_health_score: Current soil health score (0-100)
            farmer_preference: 'organic', 'chemical', or 'balanced'

        Returns:
            Balanced fertilizer recommendations
        """
        logger.info(
            f"Balancing organic/chemical fertilizers, soil health: {soil_health_score}, preference: {farmer_preference}"
        )

        # Determine organic ratio based on soil health and preference
        if farmer_preference == "organic":
            base_organic_ratio = 0.6
        elif farmer_preference == "chemical":
            base_organic_ratio = 0.2
        else:  # balanced
            base_organic_ratio = 0.35

        # Adjust based on soil health
        if soil_health_score < 50:
            # Poor soil health - increase organic ratio
            organic_ratio = min(0.7, base_organic_ratio + 0.2)
            reason = "Increased organic fertilizers recommended due to poor soil health"
        elif soil_health_score < 70:
            # Moderate soil health - slight increase
            organic_ratio = min(0.6, base_organic_ratio + 0.1)
            reason = "Moderate organic fertilizer ratio for soil health improvement"
        else:
            # Good soil health - use base ratio
            organic_ratio = base_organic_ratio
            reason = "Balanced fertilizer ratio suitable for healthy soil"

        # Generate recommendations with optimized ratio
        recommendations = self.generate_fertilizer_recommendations(
            nutrient_requirements, organic_preference=organic_ratio
        )

        recommendations["balancing_strategy"] = {
            "soil_health_score": soil_health_score,
            "farmer_preference": farmer_preference,
            "organic_ratio": organic_ratio,
            "chemical_ratio": 1 - organic_ratio,
            "reason": reason,
            "soil_health_benefits": self._get_soil_health_benefits(organic_ratio),
            "cost_efficiency": self._get_cost_efficiency_note(organic_ratio),
        }

        logger.info(f"Balanced plan: {organic_ratio:.1%} organic, {(1-organic_ratio):.1%} chemical")

        return recommendations

    def _get_soil_health_benefits(self, organic_ratio: float) -> str:
        """Get soil health benefits description"""
        if organic_ratio >= 0.5:
            return "High organic content will significantly improve soil structure, water retention, and microbial activity"
        elif organic_ratio >= 0.3:
            return "Moderate organic content will maintain soil health and provide sustained nutrient release"
        else:
            return "Lower organic content focuses on immediate nutrient availability. Consider increasing organic inputs over time."

    def _get_cost_efficiency_note(self, organic_ratio: float) -> str:
        """Get cost efficiency note"""
        if organic_ratio >= 0.5:
            return "Higher initial cost but long-term soil health benefits reduce future fertilizer needs"
        elif organic_ratio >= 0.3:
            return "Balanced cost with good soil health benefits"
        else:
            return "Lower cost with immediate results but may require more frequent applications"

    def generate_complete_fertilizer_plan(
        self,
        crop_type: str,
        area_hectares: float,
        soil_data: Dict[str, Any],
        planting_date: date,
        budget_per_hectare: Optional[float] = None,
        farmer_preference: str = "balanced",
        target_yield_factor: float = 1.0,
        weather_forecast: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete fertilizer plan with all optimizations

        This is the main entry point that combines all fertilizer recommendation features.

        Args:
            crop_type: Type of crop
            area_hectares: Area in hectares
            soil_data: Current soil test data
            planting_date: Planting date
            budget_per_hectare: Optional budget constraint
            farmer_preference: 'organic', 'chemical', or 'balanced'
            target_yield_factor: Target yield multiplier
            weather_forecast: Optional weather forecast data

        Returns:
            Complete fertilizer plan with recommendations, timing, and cost
        """
        logger.info(f"Generating complete fertilizer plan for {crop_type} on {area_hectares} ha")

        # Step 1: Calculate nutrient requirements
        nutrient_req = self.calculate_nutrient_requirements(
            crop_type, area_hectares, soil_data, target_yield_factor
        )

        # Step 2: Get soil health score
        soil_health_score = soil_data.get("soil_health_score", 60.0)

        # Step 3: Generate balanced recommendations
        if budget_per_hectare:
            # Budget-constrained optimization
            fertilizer_plan = self.optimize_for_budget(
                nutrient_req, budget_per_hectare, min_organic_ratio=0.2
            )
        else:
            # Balance organic/chemical based on soil health and preference
            fertilizer_plan = self.balance_organic_chemical(
                nutrient_req, soil_health_score, farmer_preference
            )

        # Step 4: Optimize application timing
        timing_plan = self.optimize_application_timing(
            crop_type, planting_date, fertilizer_plan["recommendations"], weather_forecast
        )

        # Step 5: Compile complete plan
        complete_plan = {
            "crop_type": crop_type,
            "area_hectares": area_hectares,
            "planting_date": planting_date,
            "target_yield_factor": target_yield_factor,
            "soil_health_score": soil_health_score,
            "nutrient_requirements": nutrient_req,
            "fertilizer_recommendations": fertilizer_plan,
            "application_schedule": timing_plan,
            "cost_summary": {
                "total_cost": fertilizer_plan["total_cost"],
                "cost_per_hectare": fertilizer_plan["cost_per_hectare"],
                "within_budget": fertilizer_plan.get("within_budget", True),
                "budget_per_hectare": budget_per_hectare,
            },
            "key_recommendations": [
                f"Total fertilizer cost: ₹{fertilizer_plan['total_cost']:.2f} (₹{fertilizer_plan['cost_per_hectare']:.2f}/ha)",
                f"Organic fertilizer ratio: {fertilizer_plan['organic_ratio']:.1%}",
                f"Apply fertilizers in {len(timing_plan['schedule'])} stages over crop growth period",
                "Follow weather-based timing to avoid nutrient loss",
                "Maintain soil moisture during application for better nutrient uptake",
            ],
        }

        logger.info(f"Complete fertilizer plan generated successfully")

        return complete_plan


# Global service instance
fertilizer_service = FertilizerRecommendationService()
