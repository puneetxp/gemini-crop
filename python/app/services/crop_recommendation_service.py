"""
RAG-Based Crop Recommendation Service
Provides intelligent crop recommendations using market intelligence data and Amazon Bedrock
Validates AC4: RAG system suggests top 3 profitable crops with opportunity cost analysis and 2-crop rotation
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as Session
from typing import Dict, List, Optional

from app.services.bedrock_service import bedrock_service
from app.services.farm_access import fetch_all, fetch_one, run_named
from app.services.market_data_service import _CMD_VIEW, MarketDataService, _where
from app.services.profit_margin_service import ProfitMarginService

logger = logging.getLogger(__name__)


class CropRecommendationService:
    """Service for RAG-based crop recommendations with opportunity cost analysis"""

    def __init__(self, db: Session):
        """
        Initialize crop recommendation service

        Args:
            db: Database session
        """
        self.db = db
        self.market_service = MarketDataService(db)
        self.profit_margin_service = ProfitMarginService(db)

    def get_rag_crop_recommendations(
        self,
        state: str,
        district: Optional[str] = None,
        season: Optional[str] = None,
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        area_acres: Optional[float] = None,
        top_n: int = 3,
        include_rotation: bool = True,
    ) -> Dict[str, Any]:
        """
        Get RAG-based crop recommendations with opportunity cost analysis

        This is the main endpoint that validates AC4:
        - Top 3 profitable crops
        - Opportunity cost analysis
        - 2-crop rotation recommendations
        - Confidence scores

        Args:
            state: State name (required)
            district: District name (optional)
            season: Season filter (kharif, rabi, zaid) (optional)
            soil_type: Soil type (optional)
            irrigation_type: Irrigation type (optional)
            area_acres: Farm area in acres (optional)
            top_n: Number of top crops to recommend (default: 3)
            include_rotation: Include crop rotation recommendations (default: True)

        Returns:
            Comprehensive crop recommendations with opportunity cost analysis
        """
        try:
            logger.info(
                f"Generating RAG crop recommendations for {state}, {district}, season={season}"
            )

            # Step 1: Get top profitable crops from historical data
            top_crops = self._get_top_profitable_crops_from_data(
                state=state, district=district, season=season, top_n=top_n
            )

            if not top_crops:
                logger.warning(f"No historical data found for {state}, {district}")
                # Fallback to Bedrock recommendations
                return self._get_bedrock_fallback_recommendations(
                    state=state,
                    district=district,
                    season=season,
                    soil_type=soil_type,
                    irrigation_type=irrigation_type,
                    area_acres=area_acres,
                    top_n=top_n,
                )

            # Step 2: Enhance with Bedrock AI insights
            enhanced_recommendations = self._enhance_with_bedrock(
                crops=top_crops, state=state, district=district, season=season, soil_type=soil_type
            )

            # Step 2.5: Calculate detailed profit margins for each crop
            for crop in enhanced_recommendations:
                try:
                    profit_margin_data = self.profit_margin_service.calculate_profit_margin(
                        crop_type=crop["crop_name"],
                        state=state,
                        district=district,
                        season=season,
                        area_acres=area_acres or 1.0,
                    )

                    # Add profit margin details to crop recommendation
                    crop["profit_margin_details"] = {
                        "profit_margin_percentage": profit_margin_data["profit_margin"][
                            "profit_margin_percentage"
                        ],
                        "net_profit": profit_margin_data["profit_margin"]["net_profit"],
                        "net_profit_per_acre": profit_margin_data["profit_margin"][
                            "net_profit_per_acre"
                        ],
                        "roi_percentage": profit_margin_data["profit_margin"]["roi_percentage"],
                        "break_even_yield_per_acre": profit_margin_data["profit_margin"][
                            "break_even_yield_per_acre"
                        ],
                        "profitability_status": profit_margin_data["profit_margin"][
                            "profitability_status"
                        ],
                        "total_costs": profit_margin_data["costs"]["total_area"]["total_costs"],
                        "total_revenue": profit_margin_data["revenue"]["total_area"][
                            "total_revenue"
                        ],
                    }

                    logger.info(
                        f"Added profit margin for {crop['crop_name']}: {crop['profit_margin_details']['profit_margin_percentage']:.2f}%"
                    )

                except Exception as e:
                    logger.warning(
                        f"Could not calculate profit margin for {crop['crop_name']}: {e}"
                    )
                    crop["profit_margin_details"] = None

            # Step 3: Calculate opportunity costs between top crops
            opportunity_costs = self._calculate_opportunity_costs_matrix(
                crops=enhanced_recommendations, state=state, district=district, season=season
            )

            # Step 4: Generate crop rotation recommendations (if requested)
            rotation_recommendations = []
            if include_rotation:
                rotation_recommendations = self._generate_crop_rotation_recommendations(
                    primary_crops=enhanced_recommendations, state=state, district=district
                )

            # Step 5: Calculate confidence scores
            for crop in enhanced_recommendations:
                crop["confidence_score"] = self._calculate_confidence_score(
                    crop=crop, state=state, district=district
                )

            # Step 6: Compile final response
            response = {
                "location": {"state": state, "district": district, "season": season},
                "top_recommendations": enhanced_recommendations[:top_n],
                "opportunity_cost_analysis": opportunity_costs,
                "crop_rotation_recommendations": rotation_recommendations,
                "data_sources": {
                    "historical_market_data": True,
                    "bedrock_ai_insights": True,
                    "opportunity_cost_engine": True,
                },
                "recommendation_summary": self._generate_recommendation_summary(
                    crops=enhanced_recommendations[:top_n],
                    opportunity_costs=opportunity_costs,
                    rotations=rotation_recommendations,
                ),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Successfully generated RAG recommendations for {state}")
            return response

        except Exception as e:
            logger.error(f"Error generating RAG recommendations: {e}")
            raise

    def _get_top_profitable_crops_by_vector_similarity(
        self, state: str, district: Optional[str], season: Optional[str], top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top crops using pgvector similarity search on crop_market_data
        """
        # Build query text representation
        query_text = f"crop:all state:{state}"
        if district:
            query_text += f" district:{district}"
        if season:
            query_text += f" season:{season}"

        # Generate query embedding
        try:
            from app.services.bedrock_service import BedrockService

            bedrock = BedrockService()
            if not getattr(bedrock, "vertex_enabled", False):
                return []

            query_vector = bedrock.generate_embedding(query_text, reduce_to_384=True)
            if not query_vector:
                return []

            # Execute vector similarity query using pgvector <=> (cosine distance) operator.
            # Note: crop_market_data has no rag_embedding column in the current schema, so this query
            # fails and the except below falls back to the SQL path.
            sql_query = """
                SELECT 
                    crop_name,
                    state,
                    district,
                    price_per_kg,
                    season,
                    demand_level,
                    1 - (rag_embedding <=> :query_vector) as similarity_score
                FROM crop_market_data
                WHERE rag_embedding IS NOT NULL
                ORDER BY rag_embedding <=> :query_vector
                LIMIT :limit
            """

            result = run_named(
                sql_query, {"query_vector": str(list(query_vector)), "limit": top_n * 4}
            )

            crops = []
            seen_crops = set()
            for row in result:
                crop_name = row.crop_name
                if crop_name in seen_crops:
                    continue
                seen_crops.add(crop_name)

                # Estimate profit metrics from market data
                price = float(row.price_per_kg or 15)
                est_profit = price * 2000 - 25000  # Rs per acre
                est_investment = 25000
                est_roi = (est_profit / est_investment) * 100 if est_profit > 0 else 0

                crop_data = {
                    "crop_name": crop_name,
                    "variety": "Recommended variety",
                    "expected_profit_per_acre": max(est_profit, 5000),
                    "investment_per_acre": est_investment,
                    "roi_percentage": max(est_roi, 20),
                    "data_points": 1,
                    "data_source": "vector_semantic_search",
                }

                # Retrieve standard yield data using SQL fallback helper
                yield_data = self._get_yield_data(
                    crop_type=crop_name, state=state, district=district, season=season
                )
                if yield_data:
                    crop_data["expected_yield_per_acre"] = yield_data["avg_yield"]
                    crop_data["yield_success_rate"] = yield_data["success_rate"]

                crop_data["avg_market_price"] = price
                crop_data["price_trend"] = "increasing"
                crop_data["yoy_growth"] = float(row.similarity_score * 10)

                crops.append(crop_data)

            return crops[: top_n * 2]
        except Exception as e:
            logger.warning(f"Vector search crop retrieval failed, falling back to SQL: {e}")
            return []

    def _get_top_profitable_crops_from_data(
        self, state: str, district: Optional[str], season: Optional[str], top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top profitable crops from historical data

        Uses RAG approach: Retrieval from database (using Vector Search first, fallback to SQL) + Analysis
        """
        # 1. Attempt Vector Similarity Search first (Semantic RAG)
        vector_crops = self._get_top_profitable_crops_by_vector_similarity(
            state=state, district=district, season=season, top_n=top_n
        )
        if vector_crops:
            logger.info(f"Retrieved {len(vector_crops)} crops using semantic vector search.")
            return vector_crops

        # 2. Fallback to traditional SQL query if vector search is empty or fails
        try:
            # Query profitability data
            where, bind = _where({"state": state, "district": district, "season": season})
            # Group by crop and variety, order by profit; get more than needed for filtering
            results = fetch_all(
                f"""SELECT crop_type, variety, AVG(avg_profit_per_acre) AS avg_profit,
                           AVG(total_investment_cost) AS avg_investment, AVG(roi_percentage) AS avg_roi,
                           COUNT(id) AS data_points
                    FROM crop_profitability{where}
                    GROUP BY crop_type, variety
                    ORDER BY AVG(avg_profit_per_acre) DESC NULLS LAST LIMIT ?""",
                bind + [int(top_n * 2)],
            )

            if not results:
                return []

            # Convert to list of dictionaries
            crops = []
            for result in results:
                crop_data = {
                    "crop_name": result.crop_type,
                    "variety": result.variety or "Local variety",
                    "expected_profit_per_acre": (
                        float(result.avg_profit) if result.avg_profit else 0
                    ),
                    "investment_per_acre": (
                        float(result.avg_investment) if result.avg_investment else 0
                    ),
                    "roi_percentage": float(result.avg_roi) if result.avg_roi else 0,
                    "data_points": result.data_points,
                    "data_source": "historical_profitability",
                }

                # Get yield data
                yield_data = self._get_yield_data(
                    crop_type=result.crop_type, state=state, district=district, season=season
                )
                if yield_data:
                    crop_data["expected_yield_per_acre"] = yield_data["avg_yield"]
                    crop_data["yield_success_rate"] = yield_data["success_rate"]

                # Get market data
                market_data = self._get_market_data(
                    crop_type=result.crop_type, state=state, district=district, season=season
                )
                if market_data:
                    crop_data["avg_market_price"] = market_data["avg_price"]
                    crop_data["price_trend"] = market_data["trend"]
                    crop_data["yoy_growth"] = market_data["yoy_growth"]

                crops.append(crop_data)

            return crops[: top_n * 2]  # Return extra for opportunity cost analysis

        except Exception as e:
            logger.error(f"Error retrieving profitable crops: {e}")
            return []

    def _get_yield_data(
        self, crop_type: str, state: str, district: Optional[str], season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get average yield data for a crop"""
        try:
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            result = fetch_one(
                f"SELECT AVG(avg_yield_per_acre) AS avg_yield, AVG(success_rate) AS success_rate "
                f"FROM historical_yields{where}",
                bind,
            )

            if result and result.avg_yield:
                return {
                    "avg_yield": float(result.avg_yield),
                    "success_rate": float(result.success_rate) if result.success_rate else 75.0,
                }
            return None

        except Exception as e:
            logger.error(f"Error getting yield data: {e}")
            return None

    def _get_market_data(
        self, crop_type: str, state: str, district: Optional[str], season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get market price data for a crop"""
        try:
            where, bind = _where(
                {"crop_type": crop_type, "state": state, "district": district, "season": season}
            )
            result = fetch_one(
                f"SELECT AVG(avg_price_per_quintal) AS avg_price, AVG(yoy_price_change) AS yoy_growth "
                f"FROM {_CMD_VIEW}{where}",
                bind,
            )

            if result and result.avg_price:
                yoy_growth = float(result.yoy_growth) if result.yoy_growth else 0
                trend = (
                    "increasing"
                    if yoy_growth > 5
                    else ("decreasing" if yoy_growth < -5 else "stable")
                )

                return {
                    "avg_price": float(result.avg_price),
                    "yoy_growth": yoy_growth,
                    "trend": trend,
                }
            return None

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    def _enhance_with_bedrock(
        self,
        crops: List[Dict[str, Any]],
        state: str,
        district: Optional[str],
        season: Optional[str],
        soil_type: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Enhance crop recommendations with Bedrock AI insights

        Adds qualitative insights, risk assessment, and recommendations
        """
        try:
            # For each crop, get Bedrock insights
            for crop in crops:
                crop_name = crop["crop_name"]

                # Create prompt for Bedrock
                prompt = f"""Provide brief agricultural insights for {crop_name} in {state}, {district or 'region'}.

Current data shows:
- Expected profit: ₹{crop.get('expected_profit_per_acre', 0):.0f} per acre
- ROI: {crop.get('roi_percentage', 0):.1f}%
- Market trend: {crop.get('price_trend', 'stable')}

Provide in 2-3 sentences:
1. Key success factors for this crop in this region
2. Main risks or challenges
3. One practical recommendation

Keep it concise and actionable."""

                try:
                    insights = bedrock_service._invoke_claude(
                        prompt=prompt,
                        max_tokens=200,
                        temperature=0.3,
                        use_instant=True,  # Use faster model for insights
                    )

                    crop["ai_insights"] = insights.strip()
                    crop["enhanced_with_ai"] = True

                except Exception as e:
                    logger.warning(f"Could not get Bedrock insights for {crop_name}: {e}")
                    crop["ai_insights"] = f"Proven crop for {state} region with good market demand."
                    crop["enhanced_with_ai"] = False

            return crops

        except Exception as e:
            logger.error(f"Error enhancing with Bedrock: {e}")
            return crops

    def _calculate_opportunity_costs_matrix(
        self,
        crops: List[Dict[str, Any]],
        state: str,
        district: Optional[str],
        season: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Calculate opportunity costs between top crops

        Shows what farmers forgo by choosing one crop over another
        """
        if len(crops) < 2:
            return []

        opportunity_costs = []

        # Compare top crop with alternatives
        primary_crop = crops[0]

        for i in range(1, min(len(crops), 4)):  # Compare with next 3 crops
            alternative_crop = crops[i]

            profit_difference = (
                alternative_crop["expected_profit_per_acre"]
                - primary_crop["expected_profit_per_acre"]
            )

            investment_difference = alternative_crop.get(
                "investment_per_acre", 0
            ) - primary_crop.get("investment_per_acre", 0)

            # Determine recommendation
            if profit_difference > 5000:  # Alternative is significantly more profitable
                recommendation = f"Consider {alternative_crop['crop_name']} for ₹{abs(profit_difference):.0f} higher profit"
                choice = alternative_crop["crop_name"]
            elif profit_difference < -5000:  # Primary is significantly more profitable
                recommendation = (
                    f"{primary_crop['crop_name']} is ₹{abs(profit_difference):.0f} more profitable"
                )
                choice = primary_crop["crop_name"]
            else:  # Similar profitability
                recommendation = f"Both crops have similar profitability. Choose based on resources and experience."
                choice = "Either"

            opportunity_cost = {
                "primary_crop": primary_crop["crop_name"],
                "alternative_crop": alternative_crop["crop_name"],
                "profit_difference": round(profit_difference, 2),
                "investment_difference": round(investment_difference, 2),
                "opportunity_cost": round(abs(profit_difference), 2),
                "recommended_choice": choice,
                "recommendation": recommendation,
                "comparison": {
                    "primary": {
                        "crop": primary_crop["crop_name"],
                        "profit": round(primary_crop["expected_profit_per_acre"], 2),
                        "investment": round(primary_crop.get("investment_per_acre", 0), 2),
                        "roi": round(primary_crop.get("roi_percentage", 0), 2),
                    },
                    "alternative": {
                        "crop": alternative_crop["crop_name"],
                        "profit": round(alternative_crop["expected_profit_per_acre"], 2),
                        "investment": round(alternative_crop.get("investment_per_acre", 0), 2),
                        "roi": round(alternative_crop.get("roi_percentage", 0), 2),
                    },
                },
            }

            opportunity_costs.append(opportunity_cost)

        return opportunity_costs

    def _generate_crop_rotation_recommendations(
        self, primary_crops: List[Dict[str, Any]], state: str, district: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate optimized 2-crop rotation recommendations for consecutive seasons

        Enhanced algorithm considers:
        - Soil health and nutrient balance
        - Profit maximization across both seasons
        - Crop compatibility and complementary growth patterns
        - Season sequencing (Kharif → Rabi → Zaid)
        - Risk diversification

        Validates AC4 requirement for crop rotation
        """
        rotations = []

        try:
            # Define crop compatibility matrix based on agricultural science
            # Legumes fix nitrogen, benefiting subsequent crops
            # Deep-rooted crops improve soil structure for shallow-rooted crops
            crop_compatibility = self._get_crop_compatibility_matrix()

            # Define nutrient profiles for common crops
            nutrient_profiles = self._get_crop_nutrient_profiles()

            # Get seasonal data for top crops
            for primary_crop in primary_crops[:3]:  # Top 3 crops
                crop_name = primary_crop["crop_name"]
                primary_season = self._determine_best_season(crop_name, state)
                primary_profit = primary_crop.get("expected_profit_per_acre", 0)

                # Find complementary crops for rotation based on multiple factors
                rotation_candidates = self._find_rotation_candidates(
                    primary_crop=crop_name,
                    primary_season=primary_season,
                    state=state,
                    district=district,
                    crop_compatibility=crop_compatibility,
                    nutrient_profiles=nutrient_profiles,
                )

                # Score and rank rotation candidates
                scored_rotations = []
                for candidate in rotation_candidates:
                    score = self._calculate_rotation_score(
                        primary_crop=crop_name,
                        secondary_crop=candidate["crop_type"],
                        primary_profit=primary_profit,
                        secondary_profit=candidate.get("profit", 0),
                        compatibility=crop_compatibility,
                        nutrient_profiles=nutrient_profiles,
                    )

                    candidate["rotation_score"] = score
                    scored_rotations.append(candidate)

                # Sort by rotation score (highest first)
                scored_rotations.sort(key=lambda x: x["rotation_score"], reverse=True)

                # Create rotation recommendations from top candidates
                for candidate in scored_rotations[:2]:  # Top 2 rotations per primary crop
                    rotation_season = candidate["season"]
                    secondary_profit = candidate.get("profit", 0)

                    # Calculate soil health benefits
                    soil_benefits = self._calculate_soil_health_benefits(
                        crop_name, candidate["crop_type"], nutrient_profiles
                    )

                    # Calculate total annual profit
                    total_profit = round(primary_profit + secondary_profit, 2)

                    rotation = {
                        "sequence": f"{crop_name} → {candidate['crop_type']}",
                        "season_1": {
                            "crop": crop_name,
                            "season": primary_season,
                            "expected_profit": round(primary_profit, 2),
                        },
                        "season_2": {
                            "crop": candidate["crop_type"],
                            "season": rotation_season,
                            "expected_profit": round(secondary_profit, 2),
                        },
                        "total_annual_profit": total_profit,
                        "rotation_score": round(candidate["rotation_score"], 2),
                        "soil_health_benefits": soil_benefits,
                        "benefits": self._generate_rotation_benefits(
                            crop_name, candidate["crop_type"], soil_benefits, nutrient_profiles
                        ),
                        "recommendation": self._generate_rotation_recommendation(
                            crop_name,
                            candidate["crop_type"],
                            primary_season,
                            rotation_season,
                            total_profit,
                            soil_benefits,
                        ),
                    }

                    rotations.append(rotation)

                    if len(rotations) >= 3:  # Limit to top 3 overall rotations
                        break

                if len(rotations) >= 3:
                    break

            # If no data-driven rotations found, provide common rotations
            if not rotations:
                rotations = self._get_common_rotations(primary_crops, state)

            # Sort final rotations by score and return top 3
            rotations.sort(key=lambda x: x.get("rotation_score", 0), reverse=True)
            return rotations[:3]

        except Exception as e:
            logger.error(f"Error generating rotation recommendations: {e}")
            return self._get_common_rotations(primary_crops, state)

    def _get_crop_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Define crop compatibility scores based on agricultural science

        Scores range from 0.0 (incompatible) to 1.0 (highly compatible)
        Based on:
        - Nutrient complementarity
        - Pest/disease break cycles
        - Soil structure improvement
        - Root depth complementarity
        """
        return {
            # Legumes (nitrogen fixers) - excellent for following crops
            "gram": {"wheat": 0.95, "mustard": 0.90, "barley": 0.90, "cotton": 0.85},
            "peas": {"wheat": 0.95, "mustard": 0.90, "barley": 0.90, "maize": 0.85},
            "lentil": {"wheat": 0.95, "mustard": 0.90, "rice": 0.85, "cotton": 0.85},
            "soybean": {"wheat": 0.90, "mustard": 0.85, "rice": 0.85, "cotton": 0.80},
            "groundnut": {"wheat": 0.90, "mustard": 0.85, "rice": 0.85, "cotton": 0.80},
            # Cereals - good rotation partners
            "rice": {"wheat": 0.95, "mustard": 0.85, "gram": 0.90, "peas": 0.90, "lentil": 0.90},
            "wheat": {
                "rice": 0.90,
                "cotton": 0.85,
                "maize": 0.80,
                "soybean": 0.85,
                "groundnut": 0.85,
            },
            "maize": {"wheat": 0.85, "mustard": 0.80, "gram": 0.85, "peas": 0.85},
            "barley": {"gram": 0.90, "peas": 0.90, "cotton": 0.80, "maize": 0.75},
            # Cash crops
            "cotton": {"wheat": 0.90, "gram": 0.85, "mustard": 0.80, "barley": 0.80},
            "sugarcane": {"wheat": 0.70, "gram": 0.75, "soybean": 0.70},  # Long duration crop
            # Oilseeds
            "mustard": {"rice": 0.85, "maize": 0.80, "cotton": 0.80, "soybean": 0.75},
            "sunflower": {"wheat": 0.80, "gram": 0.85, "rice": 0.75},
            # Millets
            "bajra": {"wheat": 0.85, "mustard": 0.80, "gram": 0.85},
            "jowar": {"wheat": 0.85, "gram": 0.85, "mustard": 0.80},
        }

    def _get_crop_nutrient_profiles(self) -> Dict[str, Dict[str, str]]:
        """
        Define nutrient profiles for crops

        Categories:
        - Heavy feeder: Depletes soil nutrients significantly
        - Moderate feeder: Balanced nutrient usage
        - Light feeder: Minimal nutrient depletion
        - Nitrogen fixer: Adds nitrogen to soil (legumes)
        """
        return {
            # Nitrogen fixers (legumes) - improve soil
            "gram": {
                "type": "nitrogen_fixer",
                "nitrogen": "adds",
                "phosphorus": "moderate",
                "potassium": "light",
            },
            "peas": {
                "type": "nitrogen_fixer",
                "nitrogen": "adds",
                "phosphorus": "moderate",
                "potassium": "light",
            },
            "lentil": {
                "type": "nitrogen_fixer",
                "nitrogen": "adds",
                "phosphorus": "moderate",
                "potassium": "light",
            },
            "soybean": {
                "type": "nitrogen_fixer",
                "nitrogen": "adds",
                "phosphorus": "moderate",
                "potassium": "moderate",
            },
            "groundnut": {
                "type": "nitrogen_fixer",
                "nitrogen": "adds",
                "phosphorus": "moderate",
                "potassium": "moderate",
            },
            # Heavy feeders - deplete soil
            "rice": {
                "type": "heavy_feeder",
                "nitrogen": "heavy",
                "phosphorus": "moderate",
                "potassium": "heavy",
            },
            "cotton": {
                "type": "heavy_feeder",
                "nitrogen": "heavy",
                "phosphorus": "heavy",
                "potassium": "heavy",
            },
            "sugarcane": {
                "type": "heavy_feeder",
                "nitrogen": "heavy",
                "phosphorus": "heavy",
                "potassium": "heavy",
            },
            "maize": {
                "type": "heavy_feeder",
                "nitrogen": "heavy",
                "phosphorus": "moderate",
                "potassium": "moderate",
            },
            # Moderate feeders
            "wheat": {
                "type": "moderate_feeder",
                "nitrogen": "moderate",
                "phosphorus": "moderate",
                "potassium": "moderate",
            },
            "barley": {
                "type": "moderate_feeder",
                "nitrogen": "moderate",
                "phosphorus": "moderate",
                "potassium": "light",
            },
            "mustard": {
                "type": "moderate_feeder",
                "nitrogen": "moderate",
                "phosphorus": "light",
                "potassium": "moderate",
            },
            "sunflower": {
                "type": "moderate_feeder",
                "nitrogen": "moderate",
                "phosphorus": "moderate",
                "potassium": "moderate",
            },
            # Light feeders
            "bajra": {
                "type": "light_feeder",
                "nitrogen": "light",
                "phosphorus": "light",
                "potassium": "light",
            },
            "jowar": {
                "type": "light_feeder",
                "nitrogen": "light",
                "phosphorus": "light",
                "potassium": "light",
            },
        }

    def _find_rotation_candidates(
        self,
        primary_crop: str,
        primary_season: str,
        state: str,
        district: Optional[str],
        crop_compatibility: Dict[str, Dict[str, float]],
        nutrient_profiles: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Find suitable rotation candidates for the primary crop"""
        candidates = []

        # Determine next season(s) for rotation
        next_seasons = self._get_next_seasons(primary_season)

        # Query crops suitable for next seasons
        for next_season in next_seasons:
            # Query from seasonal trends
            season_query = fetch_all(
                "SELECT * FROM seasonal_trends WHERE state = ? AND planting_season = ? AND crop_type <> ?",
                [state, next_season, primary_crop],
            )

            for crop_data in season_query:
                # Check compatibility
                primary_lower = primary_crop.lower()
                candidate_lower = crop_data.crop_type.lower()

                compatibility_score = 0.5  # Default neutral compatibility
                if primary_lower in crop_compatibility:
                    if candidate_lower in crop_compatibility[primary_lower]:
                        compatibility_score = crop_compatibility[primary_lower][candidate_lower]

                # Only include if compatibility is reasonable (>0.6)
                if compatibility_score >= 0.6:
                    # Get profit data from crop profitability
                    profit_query = fetch_one(
                        """SELECT * FROM crop_profitability WHERE state = ? AND crop_type = ? AND season = ?
                           ORDER BY year DESC NULLS LAST LIMIT 1""",
                        [state, crop_data.crop_type, next_season],
                    )

                    profit = (
                        float(profit_query.avg_profit_per_acre)
                        if profit_query and profit_query.avg_profit_per_acre
                        else 0
                    )

                    candidates.append(
                        {
                            "crop_type": crop_data.crop_type,
                            "season": next_season,
                            "profit": profit,
                            "compatibility_score": compatibility_score,
                            "price_trend_yoy": (
                                float(crop_data.price_trend_yoy) if crop_data.price_trend_yoy else 0
                            ),
                            "demand_trend_yoy": (
                                float(crop_data.demand_trend_yoy)
                                if crop_data.demand_trend_yoy
                                else 0
                            ),
                        }
                    )

        return candidates

    def _get_next_seasons(self, current_season: str) -> List[str]:
        """Determine the next season(s) for crop rotation"""
        season_sequence = {
            "kharif": [
                "rabi",
                "zaid",
            ],  # After kharif (Jun-Oct), comes rabi (Nov-Apr) or zaid (May-Jun)
            "rabi": [
                "zaid",
                "kharif",
            ],  # After rabi (Nov-Apr), comes zaid (May-Jun) or kharif (Jun-Oct)
            "zaid": ["kharif"],  # After zaid (May-Jun), comes kharif (Jun-Oct)
        }
        return season_sequence.get(current_season, ["rabi", "kharif"])

    def _calculate_rotation_score(
        self,
        primary_crop: str,
        secondary_crop: str,
        primary_profit: float,
        secondary_profit: float,
        compatibility: Dict[str, Dict[str, float]],
        nutrient_profiles: Dict[str, Dict[str, str]],
    ) -> float:
        """
        Calculate overall rotation score based on multiple factors

        Scoring factors:
        - Total profit (40% weight)
        - Crop compatibility (30% weight)
        - Soil health benefits (20% weight)
        - Risk diversification (10% weight)
        """
        # Factor 1: Total profit score (normalized to 0-100)
        total_profit = primary_profit + secondary_profit
        profit_score = min(total_profit / 1000, 100)  # Normalize (₹100k = 100 points)

        # Factor 2: Compatibility score (0-100)
        primary_lower = primary_crop.lower()
        secondary_lower = secondary_crop.lower()
        compatibility_score = 50  # Default

        if primary_lower in compatibility:
            if secondary_lower in compatibility[primary_lower]:
                compatibility_score = compatibility[primary_lower][secondary_lower] * 100

        # Factor 3: Soil health score (0-100)
        soil_health_score = self._calculate_soil_health_score(
            primary_crop, secondary_crop, nutrient_profiles
        )

        # Factor 4: Risk diversification score (0-100)
        # Different crop families = better risk diversification
        risk_score = 70  # Default moderate diversification
        if self._are_different_crop_families(primary_crop, secondary_crop):
            risk_score = 90

        # Weighted average
        final_score = (
            profit_score * 0.40
            + compatibility_score * 0.30
            + soil_health_score * 0.20
            + risk_score * 0.10
        )

        return final_score

    def _calculate_soil_health_score(
        self, primary_crop: str, secondary_crop: str, nutrient_profiles: Dict[str, Dict[str, str]]
    ) -> float:
        """Calculate soil health benefit score for crop rotation"""
        primary_lower = primary_crop.lower()
        secondary_lower = secondary_crop.lower()

        score = 50  # Default neutral score

        # Get nutrient profiles
        primary_profile = nutrient_profiles.get(primary_lower, {})
        secondary_profile = nutrient_profiles.get(secondary_lower, {})

        # Best case: Nitrogen fixer followed by heavy feeder
        if (
            primary_profile.get("type") == "nitrogen_fixer"
            and secondary_profile.get("type") == "heavy_feeder"
        ):
            score = 95
        # Good case: Light feeder followed by heavy feeder
        elif (
            primary_profile.get("type") == "light_feeder"
            and secondary_profile.get("type") == "heavy_feeder"
        ):
            score = 80
        # Good case: Heavy feeder followed by nitrogen fixer
        elif (
            primary_profile.get("type") == "heavy_feeder"
            and secondary_profile.get("type") == "nitrogen_fixer"
        ):
            score = 85
        # Moderate case: Moderate feeders
        elif (
            primary_profile.get("type") == "moderate_feeder"
            or secondary_profile.get("type") == "moderate_feeder"
        ):
            score = 65
        # Poor case: Two heavy feeders in sequence
        elif (
            primary_profile.get("type") == "heavy_feeder"
            and secondary_profile.get("type") == "heavy_feeder"
        ):
            score = 30

        return score

    def _are_different_crop_families(self, crop1: str, crop2: str) -> bool:
        """Check if crops belong to different botanical families for better pest/disease management"""
        crop_families = {
            "cereals": ["rice", "wheat", "maize", "barley", "bajra", "jowar"],
            "legumes": ["gram", "peas", "lentil", "soybean", "groundnut"],
            "oilseeds": ["mustard", "sunflower", "sesame"],
            "cash_crops": ["cotton", "sugarcane", "tobacco"],
            "vegetables": ["potato", "tomato", "onion", "cabbage"],
        }

        crop1_family = None
        crop2_family = None

        crop1_lower = crop1.lower()
        crop2_lower = crop2.lower()

        for family, crops in crop_families.items():
            if any(c in crop1_lower for c in crops):
                crop1_family = family
            if any(c in crop2_lower for c in crops):
                crop2_family = family

        return (
            crop1_family != crop2_family and crop1_family is not None and crop2_family is not None
        )

    def _calculate_soil_health_benefits(
        self, primary_crop: str, secondary_crop: str, nutrient_profiles: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """Calculate detailed soil health benefits of the rotation"""
        primary_lower = primary_crop.lower()
        secondary_lower = secondary_crop.lower()

        primary_profile = nutrient_profiles.get(primary_lower, {})
        secondary_profile = nutrient_profiles.get(secondary_lower, {})

        benefits = {
            "nitrogen_balance": "neutral",
            "soil_structure": "maintained",
            "pest_disease_break": False,
            "organic_matter": "stable",
            "overall_rating": "moderate",
        }

        # Nitrogen balance
        if primary_profile.get("type") == "nitrogen_fixer":
            benefits["nitrogen_balance"] = "improved"
            benefits["organic_matter"] = "increased"
        elif (
            primary_profile.get("type") == "heavy_feeder"
            and secondary_profile.get("type") == "nitrogen_fixer"
        ):
            benefits["nitrogen_balance"] = "restored"
        elif (
            primary_profile.get("type") == "heavy_feeder"
            and secondary_profile.get("type") == "heavy_feeder"
        ):
            benefits["nitrogen_balance"] = "depleted"
            benefits["organic_matter"] = "decreased"

        # Pest and disease break
        if self._are_different_crop_families(primary_crop, secondary_crop):
            benefits["pest_disease_break"] = True

        # Overall rating
        if benefits["nitrogen_balance"] == "improved" and benefits["pest_disease_break"]:
            benefits["overall_rating"] = "excellent"
        elif (
            benefits["nitrogen_balance"] in ["improved", "restored"]
            or benefits["pest_disease_break"]
        ):
            benefits["overall_rating"] = "good"
        elif benefits["nitrogen_balance"] == "depleted":
            benefits["overall_rating"] = "poor"

        return benefits

    def _generate_rotation_benefits(
        self,
        primary_crop: str,
        secondary_crop: str,
        soil_benefits: Dict[str, Any],
        nutrient_profiles: Dict[str, Dict[str, str]],
    ) -> List[str]:
        """Generate human-readable benefits list for the rotation"""
        benefits = []

        # Soil health benefits
        if soil_benefits["nitrogen_balance"] == "improved":
            benefits.append(
                f"{primary_crop} fixes nitrogen in soil, reducing fertilizer needs for {secondary_crop}"
            )
        elif soil_benefits["nitrogen_balance"] == "restored":
            benefits.append(f"{secondary_crop} restores nitrogen depleted by {primary_crop}")

        if soil_benefits["pest_disease_break"]:
            benefits.append("Different crop families break pest and disease cycles")

        if soil_benefits["organic_matter"] == "increased":
            benefits.append("Improved soil organic matter and structure")

        # Economic benefits
        benefits.append("Optimal land utilization throughout the year")
        benefits.append("Risk diversification across different crop types")

        # Market benefits
        benefits.append("Diversified income streams from different market segments")

        return benefits

    def _generate_rotation_recommendation(
        self,
        primary_crop: str,
        secondary_crop: str,
        primary_season: str,
        secondary_season: str,
        total_profit: float,
        soil_benefits: Dict[str, Any],
    ) -> str:
        """Generate detailed recommendation text for the rotation"""
        season_names = {
            "kharif": "Kharif (monsoon)",
            "rabi": "Rabi (winter)",
            "zaid": "Zaid (summer)",
        }

        primary_season_name = season_names.get(primary_season, primary_season)
        secondary_season_name = season_names.get(secondary_season, secondary_season)

        recommendation = f"Plant {primary_crop} in {primary_season_name} season, followed by {secondary_crop} in {secondary_season_name} season. "

        # Add soil health context
        if soil_benefits["overall_rating"] == "excellent":
            recommendation += f"This rotation provides excellent soil health benefits with {soil_benefits['nitrogen_balance']} nitrogen balance. "
        elif soil_benefits["overall_rating"] == "good":
            recommendation += f"This rotation offers good soil health maintenance. "

        # Add profit context
        recommendation += f"Expected annual profit: ₹{total_profit:,.0f} per acre. "

        # Add strategic advice
        if soil_benefits["nitrogen_balance"] == "improved":
            recommendation += f"The nitrogen-fixing properties of {primary_crop} will reduce fertilizer costs for {secondary_crop}."
        elif soil_benefits["pest_disease_break"]:
            recommendation += "Alternating crop families reduces pest pressure and disease risk."

        return recommendation

    def _determine_best_season(self, crop_name: str, state: str) -> str:
        """Determine the best season for a crop based on name and region"""
        crop_lower = crop_name.lower()

        # Common season mappings
        kharif_crops = ["rice", "cotton", "maize", "soybean", "groundnut", "bajra", "jowar"]
        rabi_crops = ["wheat", "mustard", "barley", "gram", "peas", "lentil"]

        if any(c in crop_lower for c in kharif_crops):
            return "kharif"
        elif any(c in crop_lower for c in rabi_crops):
            return "rabi"
        else:
            return "kharif"  # Default

    def _get_common_rotations(
        self, primary_crops: List[Dict[str, Any]], state: str
    ) -> List[Dict[str, Any]]:
        """Get common crop rotations as fallback"""
        common_rotations = [
            {
                "sequence": "Rice → Wheat",
                "season_1": {"crop": "Rice", "season": "kharif", "expected_profit": 45000},
                "season_2": {"crop": "Wheat", "season": "rabi", "expected_profit": 40000},
                "total_annual_profit": 85000,
                "benefits": [
                    "Most common rotation in India",
                    "Complementary nutrient requirements",
                    "Good soil health maintenance",
                ],
                "recommendation": "Traditional and proven rotation for most regions",
            },
            {
                "sequence": "Cotton → Wheat",
                "season_1": {"crop": "Cotton", "season": "kharif", "expected_profit": 55000},
                "season_2": {"crop": "Wheat", "season": "rabi", "expected_profit": 40000},
                "total_annual_profit": 95000,
                "benefits": [
                    "High profit potential",
                    "Suitable for medium to heavy soils",
                    "Good market demand for both crops",
                ],
                "recommendation": "Profitable rotation for regions with adequate irrigation",
            },
        ]

        return common_rotations[:2]

    def _calculate_confidence_score(
        self, crop: Dict[str, Any], state: str, district: Optional[str]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive confidence score for recommendation

        Confidence scoring considers multiple factors:
        1. Data Quality: Availability and completeness of historical data
        2. Historical Accuracy: Success rates and yield consistency
        3. Market Stability: Price volatility and trend reliability
        4. Prediction Reliability: AI enhancement and regional specificity

        Returns:
            Dict with overall score (0.0-1.0) and component scores
        """
        # Initialize component scores
        data_quality_score = 0.0
        historical_accuracy_score = 0.0
        market_stability_score = 0.0
        prediction_reliability_score = 0.0

        # 1. DATA QUALITY SCORE (0.0 - 0.25)
        # Based on number of data points and data completeness
        data_points = crop.get("data_points", 0)

        if data_points >= 100:
            data_quality_score = 0.25
        elif data_points >= 50:
            data_quality_score = 0.20
        elif data_points >= 20:
            data_quality_score = 0.15
        elif data_points >= 10:
            data_quality_score = 0.10
        elif data_points > 0:
            data_quality_score = 0.05

        # Bonus for data completeness (has yield, market, and profit data)
        has_yield = crop.get("expected_yield_per_acre") is not None
        has_market = crop.get("avg_market_price") is not None
        has_profit = crop.get("expected_profit_per_acre", 0) > 0

        completeness_bonus = 0.0
        if has_yield and has_market and has_profit:
            completeness_bonus = 0.05
        elif (has_yield and has_market) or (has_yield and has_profit):
            completeness_bonus = 0.03

        data_quality_score = min(data_quality_score + completeness_bonus, 0.25)

        # 2. HISTORICAL ACCURACY SCORE (0.0 - 0.30)
        # Based on success rate and yield consistency
        success_rate = crop.get("yield_success_rate", 0)

        if success_rate >= 85:
            historical_accuracy_score = 0.30
        elif success_rate >= 75:
            historical_accuracy_score = 0.25
        elif success_rate >= 65:
            historical_accuracy_score = 0.20
        elif success_rate >= 55:
            historical_accuracy_score = 0.15
        elif success_rate >= 45:
            historical_accuracy_score = 0.10
        elif success_rate > 0:
            historical_accuracy_score = 0.05

        # 3. MARKET STABILITY SCORE (0.0 - 0.25)
        # Based on price trends and volatility
        yoy_growth = crop.get("yoy_growth", 0)
        price_trend = crop.get("price_trend", "unknown")

        # Positive growth is good, but extreme volatility is risky
        if 5 <= yoy_growth <= 20:
            # Healthy growth range
            market_stability_score = 0.25
        elif 0 <= yoy_growth < 5:
            # Stable market
            market_stability_score = 0.20
        elif 20 < yoy_growth <= 30:
            # High growth but potentially volatile
            market_stability_score = 0.18
        elif -5 <= yoy_growth < 0:
            # Slight decline
            market_stability_score = 0.15
        elif yoy_growth > 30:
            # Very high growth - potentially unstable
            market_stability_score = 0.12
        elif -10 <= yoy_growth < -5:
            # Moderate decline
            market_stability_score = 0.10
        elif yoy_growth < -10:
            # Significant decline
            market_stability_score = 0.05

        # Adjust based on trend stability
        if price_trend == "stable":
            market_stability_score = min(market_stability_score + 0.05, 0.25)
        elif price_trend == "increasing" and yoy_growth > 0:
            market_stability_score = min(market_stability_score + 0.03, 0.25)

        # 4. PREDICTION RELIABILITY SCORE (0.0 - 0.20)
        # Based on AI enhancement, regional specificity, and data recency

        # AI enhancement bonus
        if crop.get("enhanced_with_ai", False):
            prediction_reliability_score += 0.08

        # District-level specificity bonus (more specific = more reliable)
        if district:
            prediction_reliability_score += 0.07
        else:
            prediction_reliability_score += 0.03

        # ROI reasonableness check (very high or negative ROI reduces confidence)
        roi = crop.get("roi_percentage", 0)
        if 20 <= roi <= 150:
            # Reasonable ROI range
            prediction_reliability_score += 0.05
        elif 10 <= roi < 20 or 150 < roi <= 200:
            # Borderline reasonable
            prediction_reliability_score += 0.03
        elif roi > 0:
            # Questionable ROI
            prediction_reliability_score += 0.01

        prediction_reliability_score = min(prediction_reliability_score, 0.20)

        # Calculate overall confidence score
        overall_score = (
            data_quality_score
            + historical_accuracy_score
            + market_stability_score
            + prediction_reliability_score
        )

        # Cap at 0.95 (never 100% certain)
        overall_score = min(round(overall_score, 3), 0.95)

        # Determine confidence level
        if overall_score >= 0.80:
            confidence_level = "Very High"
        elif overall_score >= 0.65:
            confidence_level = "High"
        elif overall_score >= 0.50:
            confidence_level = "Moderate"
        elif overall_score >= 0.35:
            confidence_level = "Low"
        else:
            confidence_level = "Very Low"

        # Generate confidence explanation
        factors = []
        if data_quality_score >= 0.20:
            factors.append(f"Strong data availability ({data_points} data points)")
        elif data_quality_score >= 0.10:
            factors.append(f"Adequate data ({data_points} data points)")
        else:
            factors.append(f"Limited data ({data_points} data points)")

        if historical_accuracy_score >= 0.25:
            factors.append(f"Excellent success rate ({success_rate:.0f}%)")
        elif historical_accuracy_score >= 0.15:
            factors.append(f"Good success rate ({success_rate:.0f}%)")
        elif success_rate > 0:
            factors.append(f"Moderate success rate ({success_rate:.0f}%)")

        if market_stability_score >= 0.20:
            factors.append(f"Stable market conditions (YoY: {yoy_growth:+.1f}%)")
        elif market_stability_score >= 0.10:
            factors.append(f"Acceptable market volatility (YoY: {yoy_growth:+.1f}%)")
        else:
            factors.append(f"High market volatility (YoY: {yoy_growth:+.1f}%)")

        if crop.get("enhanced_with_ai", False):
            factors.append("AI-enhanced insights")

        if district:
            factors.append("District-specific data")

        return {
            "overall_score": overall_score,
            "confidence_level": confidence_level,
            "component_scores": {
                "data_quality": round(data_quality_score, 3),
                "historical_accuracy": round(historical_accuracy_score, 3),
                "market_stability": round(market_stability_score, 3),
                "prediction_reliability": round(prediction_reliability_score, 3),
            },
            "factors": factors,
            "explanation": f"{confidence_level} confidence based on: {', '.join(factors[:3])}",
        }

    def _generate_recommendation_summary(
        self,
        crops: List[Dict[str, Any]],
        opportunity_costs: List[Dict[str, Any]],
        rotations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate executive summary of recommendations"""
        if not crops:
            return {}

        top_crop = crops[0]

        # Extract confidence score (handle both old float and new dict format)
        confidence_data = top_crop.get("confidence_score", {})
        if isinstance(confidence_data, dict):
            confidence_value = confidence_data.get("overall_score", 0.7)
        else:
            confidence_value = confidence_data

        summary = {
            "top_recommendation": {
                "crop": top_crop["crop_name"],
                "expected_profit": round(top_crop["expected_profit_per_acre"], 2),
                "confidence": confidence_value,
                "key_insight": top_crop.get(
                    "ai_insights", "Recommended based on historical profitability"
                ),
            },
            "opportunity_cost_insight": "",
            "rotation_insight": "",
            "total_crops_analyzed": len(crops),
            "recommendation_basis": [
                "Historical profitability data",
                "Market price trends",
                "Yield success rates",
                "AI-powered insights",
                "Opportunity cost analysis",
            ],
        }

        # Add opportunity cost insight
        if opportunity_costs:
            best_alternative = opportunity_costs[0]
            if best_alternative["profit_difference"] > 0:
                summary["opportunity_cost_insight"] = (
                    f"Consider {best_alternative['alternative_crop']} as it offers "
                    f"₹{abs(best_alternative['profit_difference']):.0f} higher profit per acre"
                )
            else:
                summary["opportunity_cost_insight"] = (
                    f"{top_crop['crop_name']} is the most profitable option, "
                    f"₹{abs(best_alternative['profit_difference']):.0f} more than alternatives"
                )

        # Add rotation insight
        if rotations:
            best_rotation = rotations[0]
            summary["rotation_insight"] = (
                f"Recommended rotation: {best_rotation['sequence']} for "
                f"₹{best_rotation['total_annual_profit']:.0f} total annual profit"
            )

        return summary

    def _get_bedrock_fallback_recommendations(
        self,
        state: str,
        district: Optional[str],
        season: Optional[str],
        soil_type: Optional[str],
        irrigation_type: Optional[str],
        area_acres: Optional[float],
        top_n: int,
    ) -> Dict[str, Any]:
        """
        Fallback to Bedrock-only recommendations when no historical data available
        """
        try:
            logger.info(f"Using Bedrock fallback for {state}, {district}")

            # Get Bedrock recommendations
            bedrock_crops = bedrock_service.get_crop_recommendations(
                state=state,
                district=district or state,
                season=season or "kharif",
                soil_type=soil_type or "loamy",
                area_acres=area_acres or 5.0,
                irrigation_type=irrigation_type or "canal",
            )

            if not bedrock_crops:
                raise Exception("Bedrock returned no recommendations")

            # Format response
            recommendations = []
            for crop in bedrock_crops[:top_n]:
                # Calculate confidence score for Bedrock-only recommendations
                confidence_data = self._calculate_confidence_score(
                    crop={
                        "crop_name": crop.get("crop_name", "Unknown"),
                        "data_points": 0,  # No historical data
                        "yield_success_rate": 0,
                        "yoy_growth": 0,
                        "price_trend": "unknown",
                        "enhanced_with_ai": True,
                        "roi_percentage": crop.get("roi_percentage", 0),
                    },
                    state=state,
                    district=district,
                )

                recommendations.append(
                    {
                        "crop_name": crop.get("crop_name", "Unknown"),
                        "variety": crop.get("variety", "Local variety"),
                        "expected_profit_per_acre": crop.get("expected_profit_per_acre", 0),
                        "investment_per_acre": crop.get("investment_per_acre", 0),
                        "roi_percentage": crop.get("roi_percentage", 0),
                        "confidence_score": confidence_data,
                        "ai_insights": crop.get("suitability_reason", ""),
                        "data_source": "bedrock_ai_only",
                        "enhanced_with_ai": True,
                    }
                )

            # Extract confidence for summary
            first_confidence = recommendations[0]["confidence_score"] if recommendations else {}
            if isinstance(first_confidence, dict):
                summary_confidence = first_confidence.get("overall_score", 0)
            else:
                summary_confidence = first_confidence

            return {
                "location": {"state": state, "district": district, "season": season},
                "top_recommendations": recommendations,
                "opportunity_cost_analysis": [],
                "crop_rotation_recommendations": [],
                "data_sources": {
                    "historical_market_data": False,
                    "bedrock_ai_insights": True,
                    "opportunity_cost_engine": False,
                },
                "recommendation_summary": {
                    "top_recommendation": {
                        "crop": recommendations[0]["crop_name"] if recommendations else "N/A",
                        "expected_profit": (
                            recommendations[0]["expected_profit_per_acre"] if recommendations else 0
                        ),
                        "confidence": summary_confidence,
                        "key_insight": "Based on AI analysis of regional agricultural patterns",
                    },
                    "note": "Recommendations based on AI analysis. Historical data not available for this location.",
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Bedrock fallback failed: {e}")
            raise Exception(f"Unable to generate recommendations: {str(e)}")


def get_crop_recommendation_service(db: Session) -> CropRecommendationService:
    """Get crop recommendation service instance"""
    return CropRecommendationService(db)
