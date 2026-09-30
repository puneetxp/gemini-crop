"""
Livestock Nutrition Advisor Service
AI-powered nutrition recommendations using Amazon Bedrock

Task 28.1: Implement AI-powered nutrition advisor
- Personalized feeding recommendations based on livestock type, age, purpose, weight
- Feed cost optimization engine to meet nutritional requirements at minimum cost
- Nutritional planning for different growth stages (calf, adult, lactating)
- Feed efficiency reports with cost per kg gain and recommendations
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.cache import TTL_BEDROCK_API, get_cache_manager
from app.services.bedrock_service import bedrock_service

logger = logging.getLogger(__name__)


class LivestockNutritionService:
    """Service for AI-powered livestock nutrition recommendations"""

    def __init__(self):
        """Initialize nutrition service with Bedrock integration"""
        self.bedrock = bedrock_service

    def get_feeding_recommendations(
        self,
        species: str,
        breed: str,
        age_months: int,
        weight_kg: float,
        purpose: str,
        lactation_status: Optional[str] = None,
        milk_production_liters: Optional[float] = None,
        location_state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate personalized feeding recommendations using Bedrock AI

        Args:
            species: Livestock species (cattle, buffalo, goat, poultry)
            breed: Breed name
            age_months: Age in months
            weight_kg: Current weight in kg
            purpose: Purpose (dairy, meat, breeding, eggs)
            lactation_status: For dairy animals (dry, early_lactation, peak_lactation, late_lactation)
            milk_production_liters: Current milk production per day (for dairy)
            location_state: State for regional feed availability

        Returns:
            Comprehensive feeding recommendations with nutritional requirements
        """

        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "nutrition:feeding_recommendations",
                species=species,
                breed=breed,
                age_months=age_months,
                weight_kg=weight_kg,
                purpose=purpose,
                lactation_status=lactation_status or "",
                milk_production_liters=milk_production_liters or 0,
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for feeding recommendations: {species}, {breed}")
                return cached_result

        # Determine growth stage
        growth_stage = self._determine_growth_stage(species, age_months, lactation_status)

        prompt = f"""You are an expert livestock nutritionist. Provide comprehensive feeding recommendations for:

Livestock Details:
- Species: {species}
- Breed: {breed}
- Age: {age_months} months
- Weight: {weight_kg} kg
- Purpose: {purpose}
- Growth Stage: {growth_stage}
{f"- Lactation Status: {lactation_status}" if lactation_status else ""}
{f"- Milk Production: {milk_production_liters} liters/day" if milk_production_liters else ""}
{f"- Location: {location_state}" if location_state else ""}

Provide detailed nutritional recommendations including:

1. DAILY NUTRITIONAL REQUIREMENTS:
   - Total Dry Matter Intake (DMI) in kg
   - Crude Protein (CP) requirement in grams
   - Total Digestible Nutrients (TDN) in kg
   - Metabolizable Energy (ME) in MJ
   - Calcium (Ca) in grams
   - Phosphorus (P) in grams
   - Vitamins and minerals

2. RECOMMENDED FEED COMPOSITION:
   - Green fodder (kg/day)
   - Dry fodder (kg/day)
   - Concentrate feed (kg/day)
   - Mineral mixture (grams/day)
   - Salt (grams/day)
   - Water (liters/day)

3. FEED INGREDIENTS (with quantities):
   - List specific feed ingredients with daily quantities
   - Include locally available feeds for {location_state if location_state else 'India'}
   - Specify quality requirements

4. FEEDING SCHEDULE:
   - Number of meals per day
   - Timing of each meal
   - Order of feeding (fodder first, then concentrate, etc.)

5. SPECIAL CONSIDERATIONS:
   - Adjustments for {growth_stage} stage
   - Seasonal variations
   - Health and immunity support
   - Digestive health recommendations

6. COST ESTIMATION:
   - Approximate daily feed cost in INR
   - Monthly feed cost in INR
   - Cost breakdown by feed type

Format your response as structured JSON:
{{
  "daily_requirements": {{
    "dry_matter_intake_kg": 0.0,
    "crude_protein_grams": 0,
    "tdn_kg": 0.0,
    "metabolizable_energy_mj": 0.0,
    "calcium_grams": 0,
    "phosphorus_grams": 0,
    "vitamins_minerals": ["vitamin A", "vitamin D", "etc"]
  }},
  "feed_composition": {{
    "green_fodder_kg": 0.0,
    "dry_fodder_kg": 0.0,
    "concentrate_kg": 0.0,
    "mineral_mixture_grams": 0,
    "salt_grams": 0,
    "water_liters": 0
  }},
  "feed_ingredients": [
    {{
      "ingredient": "ingredient name",
      "quantity_kg": 0.0,
      "quality_requirement": "quality description",
      "locally_available": true
    }}
  ],
  "feeding_schedule": {{
    "meals_per_day": 3,
    "schedule": [
      {{
        "time": "6:00 AM",
        "feed_type": "Green fodder",
        "quantity": "quantity description"
      }}
    ]
  }},
  "special_considerations": [
    "consideration 1",
    "consideration 2"
  ],
  "cost_estimation": {{
    "daily_cost_inr": 0,
    "monthly_cost_inr": 0,
    "cost_breakdown": {{
      "green_fodder": 0,
      "dry_fodder": 0,
      "concentrate": 0,
      "mineral_mixture": 0
    }}
  }},
  "growth_stage": "{growth_stage}",
  "confidence_score": 0.85
}}

Provide ONLY the JSON response, no additional text."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=3000, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                recommendations = json.loads(json_text)

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, recommendations, TTL_BEDROCK_API)
                    logger.info(
                        f"Cached feeding recommendations for {species}, {breed} (6-hour TTL)"
                    )

                logger.info(f"Generated feeding recommendations for {species}, {breed}")
                return recommendations
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return self._create_fallback_recommendations(species, weight_kg, purpose)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._create_fallback_recommendations(species, weight_kg, purpose)
        except Exception as e:
            logger.error(f"Feeding recommendations error: {e}")
            raise

    def optimize_feed_cost(
        self,
        species: str,
        weight_kg: float,
        purpose: str,
        nutritional_requirements: Dict[str, Any],
        available_feeds: List[Dict[str, Any]],
        location_state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Optimize feed composition to meet nutritional requirements at minimum cost

        Args:
            species: Livestock species
            weight_kg: Current weight in kg
            purpose: Purpose (dairy, meat, breeding, eggs)
            nutritional_requirements: Required nutrients (from get_feeding_recommendations)
            available_feeds: List of available feed ingredients with prices
            location_state: State for regional feed availability

        Returns:
            Optimized feed plan with minimum cost meeting all requirements
        """

        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "nutrition:feed_optimization",
                species=species,
                weight_kg=weight_kg,
                purpose=purpose,
                requirements_hash=hash(json.dumps(nutritional_requirements, sort_keys=True)),
                feeds_hash=hash(json.dumps(available_feeds, sort_keys=True)),
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for feed optimization: {species}")
                return cached_result

        prompt = f"""You are an expert livestock nutritionist specializing in feed cost optimization. 

Livestock Details:
- Species: {species}
- Weight: {weight_kg} kg
- Purpose: {purpose}
{f"- Location: {location_state}" if location_state else ""}

Nutritional Requirements (must be met):
{json.dumps(nutritional_requirements, indent=2)}

Available Feed Ingredients:
{json.dumps(available_feeds, indent=2)}

Task: Create an optimized feed plan that:
1. Meets ALL nutritional requirements
2. Minimizes total feed cost
3. Uses locally available ingredients
4. Maintains feed palatability and digestibility
5. Ensures practical feeding implementation

Provide:
1. OPTIMIZED FEED COMPOSITION:
   - Ingredient name and daily quantity
   - Cost per ingredient
   - Nutritional contribution

2. COST ANALYSIS:
   - Total daily cost
   - Total monthly cost
   - Cost per kg of feed
   - Comparison with standard feeding (if applicable)

3. NUTRITIONAL ADEQUACY:
   - Verify all requirements are met
   - Show nutrient levels achieved vs required

4. ALTERNATIVE OPTIONS:
   - 2-3 alternative feed combinations
   - Cost-benefit comparison

Format as JSON:
{{
  "optimized_plan": {{
    "ingredients": [
      {{
        "name": "ingredient name",
        "quantity_kg": 0.0,
        "cost_inr": 0,
        "nutritional_contribution": {{
          "protein_grams": 0,
          "energy_mj": 0.0
        }}
      }}
    ],
    "total_daily_cost_inr": 0,
    "total_monthly_cost_inr": 0,
    "cost_per_kg_feed": 0.0
  }},
  "nutritional_adequacy": {{
    "protein_met": true,
    "energy_met": true,
    "minerals_met": true,
    "adequacy_percentage": 100
  }},
  "alternative_options": [
    {{
      "option_name": "Alternative 1",
      "daily_cost_inr": 0,
      "cost_difference_inr": 0,
      "trade_offs": "description"
    }}
  ],
  "cost_savings": {{
    "vs_standard_feeding": 0,
    "percentage_saved": 0.0
  }},
  "confidence_score": 0.85
}}

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=2500, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                optimization = json.loads(json_text)

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, optimization, TTL_BEDROCK_API)
                    logger.info(f"Cached feed optimization for {species} (6-hour TTL)")

                logger.info(f"Generated feed cost optimization for {species}")
                return optimization
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Feed optimization error: {e}")
            raise

    def get_growth_stage_nutrition_plan(
        self,
        species: str,
        breed: str,
        purpose: str,
        current_age_months: int,
        current_weight_kg: float,
        target_weight_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate nutritional planning for different growth stages

        Args:
            species: Livestock species
            breed: Breed name
            purpose: Purpose (dairy, meat, breeding, eggs)
            current_age_months: Current age in months
            current_weight_kg: Current weight in kg
            target_weight_kg: Target weight (for meat animals)

        Returns:
            Comprehensive nutrition plan across all growth stages
        """

        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "nutrition:growth_stage_plan",
                species=species,
                breed=breed,
                purpose=purpose,
                current_age_months=current_age_months,
                current_weight_kg=current_weight_kg,
                target_weight_kg=target_weight_kg or 0,
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for growth stage plan: {species}, {breed}")
                return cached_result

        prompt = f"""You are an expert livestock nutritionist. Create a comprehensive growth stage nutrition plan for:

Livestock Details:
- Species: {species}
- Breed: {breed}
- Purpose: {purpose}
- Current Age: {current_age_months} months
- Current Weight: {current_weight_kg} kg
{f"- Target Weight: {target_weight_kg} kg" if target_weight_kg else ""}

Provide detailed nutritional plans for each growth stage:

For {species.upper()}:
1. CALF/YOUNG STAGE (0-6 months):
   - Nutritional requirements
   - Feed composition
   - Special care requirements
   - Expected growth rate
   - Cost per month

2. GROWING STAGE (6-18 months):
   - Nutritional requirements
   - Feed composition
   - Growth targets
   - Cost per month

3. ADULT STAGE (18+ months):
   - Maintenance requirements
   - Production-specific nutrition (dairy/meat/breeding)
   - Feed composition
   - Cost per month

4. SPECIAL STAGES (if applicable):
   - Pregnancy nutrition
   - Lactation nutrition (early, peak, late)
   - Dry period nutrition

For each stage, include:
- Daily feed quantities
- Nutritional composition
- Feeding schedule
- Cost estimation
- Transition guidelines between stages

Format as JSON:
{{
  "current_stage": "stage name",
  "stages": [
    {{
      "stage_name": "Calf/Young",
      "age_range_months": "0-6",
      "nutritional_requirements": {{
        "protein_grams_per_day": 0,
        "energy_mj_per_day": 0.0,
        "calcium_grams": 0,
        "phosphorus_grams": 0
      }},
      "feed_composition": {{
        "milk_liters": 0.0,
        "starter_feed_kg": 0.0,
        "green_fodder_kg": 0.0,
        "concentrate_kg": 0.0
      }},
      "expected_growth_rate_kg_per_month": 0.0,
      "monthly_cost_inr": 0,
      "special_care": ["care point 1", "care point 2"]
    }}
  ],
  "transition_guidelines": [
    {{
      "from_stage": "Calf",
      "to_stage": "Growing",
      "transition_period_days": 14,
      "guidelines": ["guideline 1", "guideline 2"]
    }}
  ],
  "total_cost_to_maturity": 0,
  "expected_time_to_target_weight_months": 0,
  "confidence_score": 0.85
}}

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=3500, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                plan = json.loads(json_text)

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, plan, TTL_BEDROCK_API)
                    logger.info(f"Cached growth stage plan for {species}, {breed} (6-hour TTL)")

                logger.info(f"Generated growth stage nutrition plan for {species}, {breed}")
                return plan
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Growth stage plan error: {e}")
            raise

    def generate_feed_efficiency_report(
        self,
        livestock_id: int,
        species: str,
        purpose: str,
        start_weight_kg: float,
        current_weight_kg: float,
        days_elapsed: int,
        total_feed_cost_inr: float,
        milk_production_liters: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate feed efficiency report with cost per kg gain

        Args:
            livestock_id: Livestock ID
            species: Livestock species
            purpose: Purpose (dairy, meat, breeding, eggs)
            start_weight_kg: Starting weight in kg
            current_weight_kg: Current weight in kg
            days_elapsed: Days since start
            total_feed_cost_inr: Total feed cost in INR
            milk_production_liters: Average daily milk production (for dairy)

        Returns:
            Comprehensive feed efficiency report with recommendations
        """

        # Calculate basic metrics
        weight_gain_kg = current_weight_kg - start_weight_kg
        avg_daily_gain_kg = weight_gain_kg / days_elapsed if days_elapsed > 0 else 0
        cost_per_kg_gain = total_feed_cost_inr / weight_gain_kg if weight_gain_kg > 0 else 0

        prompt = f"""You are an expert livestock nutritionist. Analyze feed efficiency and provide recommendations:

Livestock Performance Data:
- Species: {species}
- Purpose: {purpose}
- Starting Weight: {start_weight_kg} kg
- Current Weight: {current_weight_kg} kg
- Weight Gain: {weight_gain_kg} kg
- Days Elapsed: {days_elapsed}
- Average Daily Gain: {avg_daily_gain_kg:.2f} kg/day
- Total Feed Cost: ₹{total_feed_cost_inr}
- Cost per kg Gain: ₹{cost_per_kg_gain:.2f}
{f"- Average Milk Production: {milk_production_liters} liters/day" if milk_production_liters else ""}

Provide comprehensive analysis:

1. FEED EFFICIENCY ASSESSMENT:
   - Compare actual vs expected daily gain for {species}
   - Feed Conversion Ratio (FCR) analysis
   - Efficiency rating (Excellent/Good/Average/Poor)

2. COST EFFICIENCY ANALYSIS:
   - Compare cost per kg gain vs industry standards
   - Cost efficiency rating
   - Potential cost savings

3. PERFORMANCE BENCHMARKS:
   - Industry standard daily gain for {species}
   - Industry standard cost per kg gain
   - Performance percentile

4. RECOMMENDATIONS:
   - Feed composition adjustments
   - Feeding schedule optimization
   - Cost reduction strategies
   - Health and management improvements

5. PROJECTED IMPROVEMENTS:
   - Expected improvement in daily gain
   - Expected cost reduction
   - Timeline for improvements

Format as JSON:
{{
  "efficiency_metrics": {{
    "weight_gain_kg": {weight_gain_kg},
    "avg_daily_gain_kg": {avg_daily_gain_kg:.3f},
    "cost_per_kg_gain_inr": {cost_per_kg_gain:.2f},
    "feed_conversion_ratio": 0.0,
    "efficiency_rating": "Good/Average/Poor"
  }},
  "benchmarks": {{
    "industry_avg_daily_gain_kg": 0.0,
    "industry_avg_cost_per_kg_inr": 0.0,
    "performance_percentile": 0
  }},
  "cost_analysis": {{
    "total_feed_cost_inr": {total_feed_cost_inr},
    "cost_efficiency_rating": "Excellent/Good/Average/Poor",
    "potential_savings_inr": 0,
    "potential_savings_percentage": 0.0
  }},
  "recommendations": [
    {{
      "category": "Feed Composition",
      "recommendation": "recommendation text",
      "expected_impact": "impact description",
      "priority": "High/Medium/Low"
    }}
  ],
  "projected_improvements": {{
    "improved_daily_gain_kg": 0.0,
    "improved_cost_per_kg_inr": 0.0,
    "timeline_days": 0,
    "expected_savings_monthly_inr": 0
  }},
  "confidence_score": 0.85
}}

Provide ONLY the JSON response."""

        try:
            response_text = self.bedrock._invoke_claude(prompt, max_tokens=2500, temperature=0.1)

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                report = json.loads(json_text)

                logger.info(f"Generated feed efficiency report for livestock {livestock_id}")
                return report
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Feed efficiency report error: {e}")
            raise

    def _determine_growth_stage(
        self, species: str, age_months: int, lactation_status: Optional[str] = None
    ) -> str:
        """Determine growth stage based on species and age"""

        if lactation_status:
            return f"lactating_{lactation_status}"

        if species in ["cattle", "buffalo"]:
            if age_months < 6:
                return "calf"
            elif age_months < 18:
                return "growing"
            else:
                return "adult"
        elif species == "goat":
            if age_months < 4:
                return "kid"
            elif age_months < 12:
                return "growing"
            else:
                return "adult"
        elif species == "poultry":
            if age_months < 2:
                return "chick"
            elif age_months < 5:
                return "growing"
            else:
                return "adult"
        else:
            return "unknown"

    def _create_fallback_recommendations(
        self, species: str, weight_kg: float, purpose: str
    ) -> Dict[str, Any]:
        """Create basic fallback recommendations when Bedrock fails"""

        # Simple fallback based on species
        if species in ["cattle", "buffalo"]:
            return {
                "daily_requirements": {
                    "dry_matter_intake_kg": weight_kg * 0.025,
                    "crude_protein_grams": int(weight_kg * 10),
                    "tdn_kg": weight_kg * 0.015,
                    "metabolizable_energy_mj": weight_kg * 0.5,
                    "calcium_grams": 50,
                    "phosphorus_grams": 30,
                    "vitamins_minerals": ["Vitamin A", "Vitamin D", "Vitamin E"],
                },
                "feed_composition": {
                    "green_fodder_kg": 20.0,
                    "dry_fodder_kg": 5.0,
                    "concentrate_kg": 3.0,
                    "mineral_mixture_grams": 50,
                    "salt_grams": 30,
                    "water_liters": 40,
                },
                "feed_ingredients": [],
                "feeding_schedule": {"meals_per_day": 3, "schedule": []},
                "special_considerations": ["Consult veterinarian for specific recommendations"],
                "cost_estimation": {
                    "daily_cost_inr": 150,
                    "monthly_cost_inr": 4500,
                    "cost_breakdown": {},
                },
                "growth_stage": "adult",
                "confidence_score": 0.5,
            }
        else:
            return {
                "daily_requirements": {},
                "feed_composition": {},
                "feed_ingredients": [],
                "feeding_schedule": {"meals_per_day": 2, "schedule": []},
                "special_considerations": ["Consult veterinarian for specific recommendations"],
                "cost_estimation": {
                    "daily_cost_inr": 50,
                    "monthly_cost_inr": 1500,
                    "cost_breakdown": {},
                },
                "growth_stage": "adult",
                "confidence_score": 0.5,
            }


# Singleton instance
nutrition_service = LivestockNutritionService()
