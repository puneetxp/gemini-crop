"""
Amazon Bedrock AI service
Handles crop intelligence, yield predictions, and agricultural recommendations

Task 18.1: Integrated Redis caching with 6-hour TTL for Bedrock API responses
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.cache import TTL_BEDROCK_API, get_cache_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """Service for Google Cloud Vertex AI foundation model operations (renamed for compatibility)"""

    def __init__(self):
        """Initialize Vertex AI runtime client"""
        import os

        from google import genai

        # Ensure credentials set up
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

        try:
            self.client = genai.Client(
                vertexai=True,
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.GOOGLE_CLOUD_REGION,
            )
            self.vertex_enabled = True
            logger.info(
                f"Vertex AI Client initialized with project {settings.GOOGLE_CLOUD_PROJECT} in region {settings.GOOGLE_CLOUD_REGION}"
            )
        except Exception as e:
            self.vertex_enabled = False
            logger.warning(
                f"Vertex AI Client initialization failed: {e}. Running in fallback/mock mode."
            )

        self.model_name = settings.GEMINI_MODEL  # defaults to gemini-3.8-flash
        self.embedding_model_name = "text-embedding-004"

    async def generate_annual_strategy(self, farm_data: Dict[str, Any]) -> str:
        """
        Generate annual crop strategy using Gemini

        Args:
            farm_data: Dictionary containing farm details, soil profiles, and region

        Returns:
            AI-generated strategy text (Markdown format)
        """
        prompt = farm_data.get("prompt", json.dumps(farm_data))

        try:
            return await self._invoke_nova(prompt)
        except Exception as e:
            logger.error(f"Annual strategy generation error: {str(e)}")
            raise

    async def _invoke_nova(
        self, prompt: str, max_tokens: int = 4096, temperature: float = 0.7
    ) -> str:
        """
        Invoke Gemini using Vertex AI
        """
        if not getattr(self, "vertex_enabled", False):
            logger.warning("Vertex AI not enabled. Returning mock generation response.")
            return "Mock Gemini Response: Vertex AI is currently uninitialized."

        try:
            from google.genai import types

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature, top_p=0.9),
            )
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI Gemini invocation failed: {str(e)}")
            raise

    def generate_embedding(self, text: str, reduce_to_384: bool = True) -> List[float]:
        """
        Generate embedding using Google Cloud Vertex AI text-embedding-004 model.
        Note: This is synchronous for compatibility with existing service calls.

        Args:
            text: Text to embed
            reduce_to_384: If True, reduces 768 dimensions to 384 for database compatibility

        Returns:
            Embedding vector
        """
        if not getattr(self, "vertex_enabled", False):
            logger.warning("Vertex AI not enabled. Returning mock embedding.")
            return [0.0] * (384 if reduce_to_384 else 768)

        try:
            from google.genai import types

            dim = 384 if reduce_to_384 else None
            config = types.EmbedContentConfig(output_dimensionality=dim) if dim else None

            response = self.client.models.embed_content(
                model=self.embedding_model_name, contents=text, config=config
            )

            if not response or not response.embeddings:
                return [0.0] * (384 if reduce_to_384 else 768)

            return response.embeddings[0].values

        except Exception as e:
            logger.error(f"Vertex AI embedding generation failed: {e}. Returning mock vector.")
            return [0.0] * (384 if reduce_to_384 else 768)

    def _invoke_claude(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.1,
        use_instant: bool = False,
    ) -> str:
        """
        Synchronous wrapper for existing calls. Uses Gemini.
        """
        if not getattr(self, "vertex_enabled", False):
            logger.warning("Vertex AI not enabled. Returning mock generation response.")
            return "Mock Gemini Response: Vertex AI is currently uninitialized."

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature, top_p=0.9),
            )
            return response.text
        except Exception as e:
            logger.error(
                f"Vertex AI Gemini sync invocation failed: {str(e)}. Returning mock response."
            )
            return "Mock Vertex AI Gemini Response: Crop match score is 90% and quality meets requirements."

    async def predict_location_from_gps(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Predict state, district, pincode, village, and soil type from GPS coordinates

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Dict containing state, district, pincode, village, primary_soil_type
        """
        # Check cache first
        cache_manager = get_cache_manager()
        cache_key = None
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:predict_location_gps", lat=round(latitude, 4), lon=round(longitude, 4)
            )
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for GPS location prediction: {latitude}, {longitude}")
                return cached_result

        prompt = f"""You are an expert in Indian Geography and Agriculture.
Given the precise GPS coordinates Latitude: {latitude}, Longitude: {longitude}, predict the likely location details and prominent soil conditions.

Answer ONLY with a valid JSON object matching the following format completely, no extra words or markdown:
{{
   "state": "State Name",
   "district": "District Name",
   "pincode": "6 Digit Pincode",
   "village": "Village/Taluka/Tehsil Name",
   "primary_soil_type": "One of: clay, sandy, loamy, silt, peat, black, red, or mixed"
}}"""

        try:
            response_text = self._invoke_claude(
                prompt, max_tokens=500, temperature=0.1, use_instant=True
            )
            logger.info(f"Raw Claude GPS Response: {response_text}")

            # Extract and parse JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])

                # Cache the JSON outcome
                if cache_manager and cache_manager.enabled and cache_key:
                    cache_manager.set(cache_key, result, TTL_BEDROCK_API)

                return result
            else:
                logger.warning("Could not parse JSON from Bedrock GPS prediction response")
                return {}
        except Exception as e:
            logger.error(f"GPS location prediction error: {e}")
            return {}

    async def predict_location_from_pincode(self, pincode: str) -> Dict[str, Any]:
        """
        Predict village, district, state, and likely soil type from a pincode

        Args:
            pincode: 6-digit Indian Pincode

        Returns:
            Dict containing state, district, village, primary_soil_type
        """
        # Check cache first
        cache_manager = get_cache_manager()
        cache_key = None
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:predict_location_pincode", pincode=pincode
            )
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for pincode prediction: {pincode}")
                return cached_result

        prompt = f"""You are an expert in Indian Geography and Agriculture.
Given the Indian Pincode {pincode}, predict the state, district, and a LIST of EXACTLY 5 prominent villages or post office names (VPO) covering that pincode. 
For each village, predict the dominant soil type.

Answer ONLY with a valid JSON object matching the following format completely, no extra words or markdown:
{{
   "state": "State Name",
   "district": "District Name",
   "villages": [
      {{"name": "Village 1", "primary_soil_type": "sandy"}},
      {{"name": "Village 2", "primary_soil_type": "loamy"}},
      {{"name": "Village 3", "primary_soil_type": "clay"}},
      {{"name": "Village 4", "primary_soil_type": "mixed"}},
      {{"name": "Village 5", "primary_soil_type": "black"}}
   ]
}}"""

        try:
            response_text = self._invoke_claude(
                prompt, max_tokens=500, temperature=0.1, use_instant=True
            )
            logger.info(f"Raw Claude Pincode Response: {response_text}")

            # Extract and parse JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])

                # Cache the JSON outcome
                if cache_manager and cache_manager.enabled and cache_key:
                    cache_manager.set(cache_key, result, TTL_BEDROCK_API)

                return result
            else:
                logger.warning("Could not parse JSON from Bedrock pincode prediction response")
                return {}
        except Exception as e:
            logger.error(f"Pincode location prediction error: {e}")
            return {}

    async def predict_location_from_village(self, pincode: str, village: str) -> Dict[str, Any]:
        """
        Predict soil type and verify details for a specific village and pincode

        Args:
            pincode: 6-digit Indian Pincode
            village: Village/VPO name

        Returns:
            Dict containing state, district, village, primary_soil_type
        """
        # Check cache first
        cache_manager = get_cache_manager()
        cache_key = None
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:predict_location_village", pincode=pincode, village=village
            )
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for village prediction: {pincode}, {village}")
                return cached_result

        prompt = f"""You are an expert in Indian Geography and Agriculture.
Given the Indian Pincode {pincode} and the village/VPO name "{village}", predict the state, district, and the dominant soil type for that specific location.

Answer ONLY with a valid JSON object matching the following format completely, no extra words or markdown:
{{
   "state": "State Name",
   "district": "District Name",
   "village": "{village}",
   "primary_soil_type": "One of: clay, sandy, loamy, silt, peat, black, red, or mixed"
}}"""

        try:
            response_text = self._invoke_claude(
                prompt, max_tokens=500, temperature=0.1, use_instant=True
            )
            logger.info(f"Raw Claude Village Response: {response_text}")

            # Extract and parse JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])

                # Cache the JSON outcome
                if cache_manager and cache_manager.enabled and cache_key:
                    cache_manager.set(cache_key, result, TTL_BEDROCK_API)

                return result
            else:
                logger.warning("Could not parse JSON from Bedrock Village prediction response")
                return {}
        except Exception as e:
            logger.error(f"Village location prediction error: {e}")
            return {}

    async def get_annual_crop_strategy(
        self,
        state: str,
        district: str,
        soil_type: str,
        area_acres: float,
        irrigation_type: str,
        user_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        previous_crops: Optional[str] = None,
        budget_per_acre: Optional[float] = None,
        preferred_crop: Optional[str] = None,
        custom_message: Optional[str] = None,
        current_date: Optional[str] = None,
        db_session: Optional[Any] = None,
        weather_forecast: Optional[Dict[str, Any]] = None,
        soil_moisture: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive annual crop strategy using Bedrock

        Task 18.1: Cached with 6-hour TTL to reduce API costs and improve response time
        Task 40.2: Integrated with AI quota system for GPS-enhanced vs pincode-based recommendations

        Args:
            state: State name
            district: District name
            soil_type: Soil type (clay, sandy, loamy, etc.)
            area_acres: Total area in acres
            irrigation_type: Irrigation type
            user_id: User ID for quota tracking (optional)
            latitude: GPS latitude for enhanced recommendations (optional)
            longitude: GPS longitude for enhanced recommendations (optional)
            previous_crops: Previous crops grown (optional)
            budget_per_acre: Budget per acre (optional)
            preferred_crop: Farmer-prioritized crop (optional)
            custom_message: Free-form context from farmer (optional)
            db_session: Database session for quota service (optional)

        Returns:
            Comprehensive annual strategy with seasonal recommendations
            Includes quota_status with remaining_quota, gps_enhanced, quota_exceeded flags
        """

        # Initialize quota tracking variables
        gps_enhanced = False
        remaining_quota = None
        quota_exceeded = False
        fallback_message = None

        # Check quota if user_id and db_session provided
        if user_id and db_session:
            from app.services.ai_quota_service import AIQuotaService

            quota_service = AIQuotaService(db_session)
            has_gps = latitude is not None and longitude is not None

            # Check quota availability
            quota_check = await quota_service.check_quota(user_id, has_gps=has_gps)
            remaining_quota = quota_check.remaining_quota

            # Determine if we can use GPS-enhanced recommendation
            if has_gps and quota_check.can_use_gps:
                gps_enhanced = True
                logger.info(
                    f"Using GPS-enhanced recommendation for user {user_id} (lat: {latitude}, lon: {longitude})"
                )
            elif has_gps and quota_check.fallback_to_pincode:
                gps_enhanced = False
                quota_exceeded = True
                fallback_message = quota_check.message
                logger.info(
                    f"Quota exceeded for user {user_id}, falling back to pincode-based recommendation"
                )
            else:
                gps_enhanced = False
                logger.info(f"Using pincode-based recommendation for user {user_id}")

        # Check cache first (include GPS status in cache key)
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:annual_strategy",
                state=state,
                district=district,
                soil_type=soil_type,
                area_acres=area_acres,
                irrigation_type=irrigation_type,
                previous_crops=previous_crops or "",
                budget_per_acre=budget_per_acre or 0,
                preferred_crop=preferred_crop or "",
                custom_message=custom_message or "",
                current_date=current_date or "",
                gps_enhanced=gps_enhanced,
                latitude=latitude if gps_enhanced else None,
                longitude=longitude if gps_enhanced else None,
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(
                    f"Cache hit for annual strategy: {state}, {district} (GPS: {gps_enhanced})"
                )
                # Add quota status to cached result
                cached_result["quota_status"] = {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }
                return cached_result

        # Build prompt with GPS enhancement if available
        location_context = f"- Location: {state}, {district}"
        if gps_enhanced and latitude and longitude:
            location_context += (
                f"\n- GPS Coordinates: {latitude}, {longitude} (precise microclimate analysis)"
            )

        farmer_context = f"\n- Farmer Context: {custom_message.strip()}" if custom_message else ""

        moisture_str = f"{soil_moisture:.2f}%" if soil_moisture is not None else "Not available"

        weather_str = "Not available"
        if weather_forecast:
            try:
                import json

                weather_str = json.dumps(weather_forecast, indent=2)
            except Exception:
                weather_str = str(weather_forecast)

        prompt = f"""You are an expert agricultural advisor for Indian farming. Provide a comprehensive annual crop strategy with weather-integrated guidance.

{"IMPORTANT: Use the GPS coordinates to provide microclimate-specific recommendations considering local elevation, terrain, and precise weather patterns." if gps_enhanced else "Provide regional recommendations based on district-level agricultural patterns."}
- Current Date: {current_date or 'Not provided'}
- Local Current Soil Moisture (at 15cm depth): {moisture_str}
- Live Weather Forecast (Next 5 Days):
{weather_str}
{farmer_context}

CRITICAL REQUIREMENT: The strategy MUST be highly relevant to the CURRENT DATE ({current_date or 'today'}) and the live weather/soil moisture conditions provided above.
- You MUST provide SPECIFIC dates for planting/seeding (e.g., 'March 15th - March 25th') and cutting/reaping/harvest windows. Do not use broad ranges like 'Mid-March'.
- Adjust the immediate sowing recommendations based on the forecast. If upcoming weather shows excessive rainfall (>20mm), explicitly advise delaying sowing.
- If current soil moisture is low, recommend water-conserving measures like mulching, drip irrigation, or choosing drought-resistant varieties.
- If a season has already passed or is near completion, acknowledge this and focus on the next available planting opportunity.
- Ensure the variety recommended is suitable for the current soil moisture and temperature conditions.

First, internally determine the agro-climatic zone for the provided location (e.g., North India, Central Plateau, Coastal South). Use that regional context throughout the response so the farmer sees guidance that matches their climate. Call this inferred zone the "regional context" and weave it into your language.

Provide detailed recommendations for:

1. KHARIF SEASON (June-October):
   - Best crop for this location and soil
   - Expected yield per acre (realistic estimate)
   - Approximate profit estimate per acre
   - Planting window (specific months)
   - Harvest timing
   - Key success factors
   - Investment required per acre
   - WEATHER INTEGRATION:
     * Seasonal weather pattern relevant to this crop (monsoon patterns, rainfall, temperature)
     * Weather-aware planting timing (when to plant based on weather conditions)
     * Weather-aware harvest timing (optimal harvest window considering weather)
     * Weather alerts for extreme conditions (heavy rain, storms, drought, heat waves)

2. RABI SEASON (November-April):
   - Optimal crop following kharif
   - Soil health considerations
   - Market demand insights
   - Expected yield and profit per acre
   - Investment requirements
   - Planting and harvest timing
   - WEATHER INTEGRATION:
     * Seasonal weather pattern (winter temperatures, rainfall, frost risk)
     * Weather-aware planting timing (temperature-based planting guidance)
     * Weather-aware harvest timing (avoiding heat stress during harvest)
     * Weather alerts (cold waves, frost, early heat waves)

3. ZAID SEASON (May-June) - if applicable:
   - Quick cash crops or fodder options
   - Water-efficient choices
   - Expected returns
   - WEATHER INTEGRATION:
     * Seasonal weather pattern (summer heat, water availability)
     * Weather-aware planting and harvest timing
     * Weather alerts (heat waves, water stress)

4. ANNUAL STRATEGY SUMMARY:
   - Total expected annual profit per acre
   - Crop rotation benefits for soil health
   - Risk mitigation strategies
   - MONTH-BY-MONTH ACTION PLAN: Provide a detailed 12-month timeline starting from the current month ({datetime.now().strftime('%B')}). Each month MUST have at least 2 region-aware actions. If the inferred region is North India and the current month is March/April/May, explicitly mention fast-maturing leafy greens (spinach, amaranth), cucurbits (cucumber, watermelon), nursery preparation for solanaceous crops, mulching/trellis work, and heat/pest mitigation steps.
   - Alternative crop options

Focus on:
- MONTHLY ACTIONABILITY: The user specifically requested that "month is better" than just seasons. Ensure the monthly action plan is the core of the strategy.
- CURRENT MONTH RELEVANCE: Prioritize what needs to be done RIGHT NOW in {datetime.now().strftime('%B')} for the detected region.
- Crops proven successful in {state}
- Traditional crops for {district} region
- Soil health and sustainability
- Practical implementation for small farmers
- Conservative profit estimates based on current market rates
- Weather-aware guidance for planting and harvest timing
- Seasonal weather patterns relevant to recommended crops

Format your response as structured JSON with the following schema:
{{
  "kharif": {{
    "recommended_crop": "crop name",
    "variety": "variety name",
    "expected_yield_per_acre": "yield in quintals",
    "expected_profit_per_acre": profit in INR,
    "investment_per_acre": investment in INR,
    "planting_window": "month range",
    "harvest_window": "month range",
    "key_success_factors": ["factor1", "factor2"],
    "confidence_score": 0.85,
    "seasonal_weather_pattern": "description of seasonal weather relevant to this crop",
    "weather_aware_planting_timing": "when to plant based on weather conditions",
    "weather_aware_harvest_timing": "optimal harvest timing considering weather",
    "weather_alerts": [
      {{
        "alert_type": "heavy_rainfall/heat_wave/cold_wave/storm/drought",
        "severity": "low/medium/high",
        "description": "description of weather threat",
        "action": "recommended action to protect crops"
      }}
    ]
  }},
  "rabi": {{
    "recommended_crop": "crop name",
    "variety": "variety name",
    "expected_yield_per_acre": "yield in quintals",
    "expected_profit_per_acre": profit in INR,
    "investment_per_acre": investment in INR,
    "planting_window": "month range",
    "harvest_window": "month range",
    "key_success_factors": ["factor1", "factor2"],
    "confidence_score": 0.85,
    "seasonal_weather_pattern": "description of seasonal weather relevant to this crop",
    "weather_aware_planting_timing": "when to plant based on weather conditions",
    "weather_aware_harvest_timing": "optimal harvest timing considering weather",
    "weather_alerts": [
      {{
        "alert_type": "cold_wave/frost/heat_wave",
        "severity": "low/medium/high",
        "description": "description of weather threat",
        "action": "recommended action to protect crops"
      }}
    ]
  }},
  "zaid": {{
    "recommended_crop": "crop name or null",
    "expected_profit_per_acre": profit in INR or 0,
    "seasonal_weather_pattern": "description if crop recommended",
    "weather_aware_planting_timing": "timing guidance if crop recommended",
    "weather_aware_harvest_timing": "timing guidance if crop recommended",
    "weather_alerts": []
  }},
  "annual_summary": {{
    "total_expected_profit_per_acre": total profit in INR,
    "total_investment_per_acre": total investment in INR,
    "roi_percentage": ROI percentage,
    "risk_level": "low/medium/high",
    "sustainability_score": 0.8
  }},
  "alternative_options": [
    {{
      "season": "kharif/rabi",
      "crop": "alternative crop name",
      "profit_difference": difference in INR,
      "risk_comparison": "comparison text"
    }}
  ],
  "monthly_action_plan": [
    {{
      "month": "month name",
      "actions": ["action1", "action2"]
    }}
  ]
}}

IMPORTANT: Include weather integration fields (seasonal_weather_pattern, weather_aware_planting_timing, weather_aware_harvest_timing, weather_alerts) for each season.

Provide ONLY the JSON response, no additional text."""

        try:
            response_text = self._invoke_claude(prompt, max_tokens=3000, temperature=0.1)

            # Try to parse JSON from response
            # Sometimes Claude adds text before/after JSON, so we need to extract it
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                strategy = json.loads(json_text)

                # Add quota status to response
                strategy["quota_status"] = {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }

                # Increment usage counter if quota service available
                if user_id and db_session:
                    from app.services.ai_quota_service import AIQuotaService

                    quota_service = AIQuotaService(db_session)
                    await quota_service.increment_usage(user_id, is_gps_enhanced=gps_enhanced)
                    logger.info(
                        f"Incremented {'GPS-enhanced' if gps_enhanced else 'pincode-based'} usage for user {user_id}"
                    )

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, strategy, TTL_BEDROCK_API)
                    logger.info(
                        f"Cached annual strategy for {state}, {district} (6-hour TTL, GPS: {gps_enhanced})"
                    )

                logger.info(
                    f"Annual crop strategy generated for {state}, {district} (GPS: {gps_enhanced})"
                )
                return strategy
            else:
                # Fallback: return structured response from text
                logger.warning("Could not parse JSON from Bedrock response, using fallback")
                with open(
                    "/Users/puneetsharma/ai-bharat-hackathon/cropsense-ai/python/failed_response.txt",
                    "w",
                ) as f:
                    f.write(f"response_text: {response_text}")
                fallback_strategy = self._create_fallback_strategy(state, district, soil_type)

                # Add quota status to fallback
                fallback_strategy["quota_status"] = {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }

                # Increment usage counter for fallback too
                if user_id and db_session:
                    from app.services.ai_quota_service import AIQuotaService

                    quota_service = AIQuotaService(db_session)
                    await quota_service.increment_usage(user_id, is_gps_enhanced=gps_enhanced)

                # Cache fallback with shorter TTL (1 hour)
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, fallback_strategy, 3600)

                return fallback_strategy

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            fallback_strategy = self._create_fallback_strategy(state, district, soil_type)

            # Add quota status to fallback
            fallback_strategy["quota_status"] = {
                "remaining_quota": remaining_quota,
                "gps_enhanced": gps_enhanced,
                "quota_exceeded": quota_exceeded,
                "fallback_message": fallback_message,
            }

            # Increment usage counter for fallback
            if user_id and db_session:
                from app.services.ai_quota_service import AIQuotaService

                quota_service = AIQuotaService(db_session)
                await quota_service.increment_usage(user_id, is_gps_enhanced=gps_enhanced)

            # Cache fallback with shorter TTL (1 hour)
            if cache_manager and cache_manager.enabled:
                cache_manager.set(cache_key, fallback_strategy, 3600)

            return fallback_strategy
        except Exception as e:
            logger.error(f"Annual strategy generation error: {e}")
            logger.warning("Using fallback strategy due to Bedrock failure")
            fallback_strategy = self._create_fallback_strategy(state, district, soil_type)

            # Add quota status to fallback
            fallback_strategy["quota_status"] = {
                "remaining_quota": remaining_quota,
                "gps_enhanced": gps_enhanced,
                "quota_exceeded": quota_exceeded,
                "fallback_message": fallback_message,
            }

            return fallback_strategy

    async def get_crop_recommendations(
        self,
        state: str,
        district: str,
        season: str,
        soil_type: str,
        area_acres: float,
        irrigation_type: str,
        user_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        current_date: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get top crop recommendations for a specific season

        Task 18.1: Cached with 6-hour TTL
        Task 40.2: Integrated with AI quota system

        Args:
            state: State name
            district: District name
            season: Season (kharif, rabi, zaid)
            soil_type: Soil type
            area_acres: Area in acres
            irrigation_type: Irrigation type
            user_id: User ID for quota tracking (optional)
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            db_session: Database session for quota service (optional)

        Returns:
            Dictionary with recommendations list and quota_status
        """

        # Initialize quota tracking
        gps_enhanced = False
        remaining_quota = None
        quota_exceeded = False
        fallback_message = None

        # Check quota if user_id and db_session provided
        if user_id and db_session:
            from app.services.ai_quota_service import AIQuotaService

            quota_service = AIQuotaService(db_session)
            has_gps = latitude is not None and longitude is not None

            quota_check = await quota_service.check_quota(user_id, has_gps=has_gps)
            remaining_quota = quota_check.remaining_quota

            if has_gps and quota_check.can_use_gps:
                gps_enhanced = True
            elif has_gps and quota_check.fallback_to_pincode:
                gps_enhanced = False
                quota_exceeded = True
                fallback_message = quota_check.message

        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:crop_recommendations",
                state=state,
                district=district,
                season=season,
                soil_type=soil_type,
                area_acres=area_acres,
                irrigation_type=irrigation_type,
                gps_enhanced=gps_enhanced,
                latitude=latitude if gps_enhanced else None,
                longitude=longitude if gps_enhanced else None,
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(
                    f"Cache hit for crop recommendations: {state}, {district}, {season} (GPS: {gps_enhanced})"
                )
                # Add quota status to cached result
                if isinstance(cached_result, list):
                    cached_result = {
                        "recommendations": cached_result,
                        "quota_status": {
                            "remaining_quota": remaining_quota,
                            "gps_enhanced": gps_enhanced,
                            "quota_exceeded": quota_exceeded,
                            "fallback_message": fallback_message,
                        },
                    }
                return cached_result

        location_context = f"Location: {state}, {district}"
        if gps_enhanced and latitude and longitude:
            location_context += (
                f"\nGPS Coordinates: {latitude}, {longitude} (precise microclimate analysis)"
            )

        prompt = f"""As an agricultural expert, recommend the top 5 most suitable crops for:
- State: {state}
- District: {district}
- Season: {season}
- Current Date: {current_date or 'Not provided'}
- Soil Type: {soil_type}
- Land Area: {area_acres} acres
- Irrigation: {irrigation_type}

CRITICAL REQUIREMENT: The recommended crops MUST be suitable for SOWING/SEEDING around the current date ({current_date or 'today'}). 
- You MUST provide SPECIFIC DATES for the planting and harvest windows (e.g., 'March 15th - March 25th' or 'March 10th - March 20th'). 
- Do not use broad ranges like 'Mid-March' or 'Early March'. 
- Do not suggest crops that are already mid-season or near harvest. Focus on crops that a farmer can start planting NOW.

{"IMPORTANT: Use GPS coordinates for microclimate-specific recommendations." if gps_enhanced else "Provide regional recommendations based on district patterns."}

For each crop, provide:
1. Crop name and specific variety
2. Detailed reason for suitability (considering soil, weather, and CURRENT DATE)
3. Expected yield per acre
4. Optimal planting window (MUST include specific days like 'March 12th - March 22nd')
5. Optimal harvest window (MUST include specific days)
6. Estimated days to harvest
7. Market demand (High/Medium/Low)
5. Investment required per acre
6. Key growing requirements
7. Common challenges and solutions
8. Market demand level (High/Medium/Low)

Rank by overall suitability considering:
- Climate compatibility
- Soil requirements
- Market stability
- Farmer success rate in this region
- Investment vs return ratio

Focus on proven crops that work well in {state}.

Format as JSON array:
[
  {{
    "rank": 1,
    "crop_name": "crop name",
    "variety": "variety name",
    "suitability_reason": "reason text",
    "expected_yield_per_acre": "yield in quintals",
    "expected_profit_per_acre": profit in INR,
    "investment_per_acre": investment in INR,
    "key_requirements": ["req1", "req2"],
    "challenges": ["challenge1", "challenge2"],
    "market_demand": "High/Medium/Low",
    "confidence_score": 0.85,
    "optimal_planting_window": "2026-03-15",
    "optimal_harvest_window": "2026-06-20",
    "days_to_harvest": 95
  }}
]

Provide ONLY the JSON array, no additional text."""

        try:
            response_text = self._invoke_claude(prompt, max_tokens=2000, temperature=0.1)

            # Extract JSON array
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                recommendations = json.loads(json_text)

                # Build response with quota status
                result = {
                    "recommendations": recommendations,
                    "quota_status": {
                        "remaining_quota": remaining_quota,
                        "gps_enhanced": gps_enhanced,
                        "quota_exceeded": quota_exceeded,
                        "fallback_message": fallback_message,
                    },
                }

                # Increment usage counter
                if user_id and db_session:
                    from app.services.ai_quota_service import AIQuotaService

                    quota_service = AIQuotaService(db_session)
                    await quota_service.increment_usage(user_id, is_gps_enhanced=gps_enhanced)

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, result, TTL_BEDROCK_API)
                    logger.info(
                        f"Cached crop recommendations for {state}, {district}, {season} (6-hour TTL, GPS: {gps_enhanced})"
                    )

                logger.info(
                    f"Crop recommendations generated for {state}, {district}, {season} (GPS: {gps_enhanced})"
                )
                return result
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return {
                    "recommendations": [],
                    "quota_status": {
                        "remaining_quota": remaining_quota,
                        "gps_enhanced": gps_enhanced,
                        "quota_exceeded": quota_exceeded,
                        "fallback_message": fallback_message,
                    },
                }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {
                "recommendations": [],
                "quota_status": {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                },
            }
        except Exception as e:
            logger.error(f"Crop recommendations error: {e}")
            logger.warning("Using fallback due to Bedrock failure")
            return {
                "recommendations": [],
                "quota_status": {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                },
            }

    async def predict_yield_and_harvest(
        self,
        crop_name: str,
        variety: str,
        state: str,
        district: str,
        planting_date: str,
        area_acres: float,
        soil_type: str,
        irrigation_type: str,
        user_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Predict crop yield and harvest date

        Task 18.1: Cached with 6-hour TTL
        Task 40.2: Integrated with AI quota system

        Args:
            crop_name: Crop name
            variety: Crop variety
            state: State name
            district: District name
            planting_date: Planting date (YYYY-MM-DD)
            area_acres: Area in acres
            soil_type: Soil type
            irrigation_type: Irrigation type
            user_id: User ID for quota tracking (optional)
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            db_session: Database session for quota service (optional)

        Returns:
            Yield prediction and harvest date with confidence intervals and quota_status
        """

        # Initialize quota tracking
        gps_enhanced = False
        remaining_quota = None
        quota_exceeded = False
        fallback_message = None

        # Check quota if user_id and db_session provided
        if user_id and db_session:
            from app.services.ai_quota_service import AIQuotaService

            quota_service = AIQuotaService(db_session)
            has_gps = latitude is not None and longitude is not None

            quota_check = await quota_service.check_quota(user_id, has_gps=has_gps)
            remaining_quota = quota_check.remaining_quota

            if has_gps and quota_check.can_use_gps:
                gps_enhanced = True
            elif has_gps and quota_check.fallback_to_pincode:
                gps_enhanced = False
                quota_exceeded = True
                fallback_message = quota_check.message

        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            cache_key = cache_manager._generate_cache_key(
                "bedrock:yield_prediction",
                crop_name=crop_name,
                variety=variety,
                state=state,
                district=district,
                planting_date=planting_date,
                area_acres=area_acres,
                soil_type=soil_type,
                irrigation_type=irrigation_type,
                gps_enhanced=gps_enhanced,
                latitude=latitude if gps_enhanced else None,
                longitude=longitude if gps_enhanced else None,
            )

            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(
                    f"Cache hit for yield prediction: {crop_name}, {state}, {district} (GPS: {gps_enhanced})"
                )
                # Add quota status to cached result
                cached_result["quota_status"] = {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }
                return cached_result

        location_context = f"Location: {state}, {district}"
        if gps_enhanced and latitude and longitude:
            location_context += (
                f"\nGPS Coordinates: {latitude}, {longitude} (precise microclimate analysis)"
            )

        prompt = f"""As an agricultural expert, predict the yield and harvest timing for:

Crop: {crop_name} ({variety})
{location_context}
Planting Date: {planting_date}
Area: {area_acres} acres
Soil Type: {soil_type}
Irrigation: {irrigation_type}

{"IMPORTANT: Use GPS coordinates for precise microclimate-based predictions." if gps_enhanced else "Provide regional predictions based on district patterns."}

Provide:
1. Expected harvest date (with ±7 day range)
2. Expected yield per acre (with min-max range)
3. Expected total yield for {area_acres} acres
4. Quality grade prediction (A/B/C)
5. Confidence level of predictions
6. Key factors affecting yield
7. Recommendations for optimal yield

Consider:
- Typical growing duration for {crop_name} in {state}
- Seasonal weather patterns
- Soil suitability
- Irrigation adequacy

Format as JSON:
{{
  "harvest_date": "YYYY-MM-DD",
  "harvest_date_range": {{"min": "YYYY-MM-DD", "max": "YYYY-MM-DD"}},
  "expected_yield_per_acre": yield in quintals,
  "yield_range": {{"min": min yield, "max": max yield}},
  "total_expected_yield": total yield in quintals,
  "quality_grade": "A/B/C",
  "confidence_score": 0.85,
  "key_factors": ["factor1", "factor2"],
  "recommendations": ["rec1", "rec2"]
}}

Provide ONLY the JSON response."""

        try:
            response_text = self._invoke_claude(prompt, max_tokens=1000, temperature=0.1)

            # Extract JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                prediction = json.loads(json_text)

                # Add quota status to prediction
                prediction["quota_status"] = {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }

                # Increment usage counter
                if user_id and db_session:
                    from app.services.ai_quota_service import AIQuotaService

                    quota_service = AIQuotaService(db_session)
                    await quota_service.increment_usage(user_id, is_gps_enhanced=gps_enhanced)

                # Cache the result with 6-hour TTL
                if cache_manager and cache_manager.enabled:
                    cache_manager.set(cache_key, prediction, TTL_BEDROCK_API)
                    logger.info(
                        f"Cached yield prediction for {crop_name} (6-hour TTL, GPS: {gps_enhanced})"
                    )

                logger.info(f"Yield prediction generated for {crop_name} (GPS: {gps_enhanced})")
                return prediction
            else:
                logger.warning("Could not parse JSON from Bedrock response")
                return {
                    "quota_status": {
                        "remaining_quota": remaining_quota,
                        "gps_enhanced": gps_enhanced,
                        "quota_exceeded": quota_exceeded,
                        "fallback_message": fallback_message,
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {
                "quota_status": {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }
            }
        except Exception as e:
            logger.error(f"Yield prediction error: {e}")
            logger.warning("Using fallback due to Bedrock failure")
            return {
                "quota_status": {
                    "remaining_quota": remaining_quota,
                    "gps_enhanced": gps_enhanced,
                    "quota_exceeded": quota_exceeded,
                    "fallback_message": fallback_message,
                }
            }

    def _create_fallback_strategy(
        self, state: str, district: str, soil_type: str
    ) -> Dict[str, Any]:
        """Create a basic fallback strategy when Bedrock fails"""

        # Simple fallback based on common crops
        return {
            "kharif": {
                "recommended_crop": "Rice" if soil_type in ["clay", "loamy"] else "Cotton",
                "variety": "Local variety",
                "expected_yield_per_acre": "20-25 quintals",
                "expected_profit_per_acre": 40000,
                "investment_per_acre": 15000,
                "planting_window": "June-July",
                "harvest_window": "October-November",
                "key_success_factors": ["Timely planting", "Adequate water", "Pest management"],
                "confidence_score": 0.6,
                "seasonal_weather_pattern": "Monsoon rainfall from June to September provides water for cultivation. Average rainfall of 700-900mm expected during growing season.",
                "weather_aware_planting_timing": "Plant after first good monsoon rains in June when soil moisture is adequate. Avoid early planting before monsoon onset.",
                "weather_aware_harvest_timing": "Complete harvest by October before monsoon withdrawal. Dry weather during harvest ensures better grain quality.",
                "weather_alerts": [
                    {
                        "alert_type": "heavy_rainfall",
                        "severity": "medium",
                        "description": "Heavy rainfall possible during monsoon season",
                        "action": "Ensure proper drainage to prevent waterlogging",
                    }
                ],
            },
            "rabi": {
                "recommended_crop": "Wheat",
                "variety": "Local variety",
                "expected_yield_per_acre": "18-22 quintals",
                "expected_profit_per_acre": 35000,
                "investment_per_acre": 12000,
                "planting_window": "November-December",
                "harvest_window": "March-April",
                "key_success_factors": [
                    "Proper irrigation",
                    "Fertilizer application",
                    "Weed control",
                ],
                "confidence_score": 0.6,
                "seasonal_weather_pattern": "Cool winter temperatures (10-25°C) ideal for wheat growth. Minimal rainfall during growing season requires irrigation.",
                "weather_aware_planting_timing": "Plant in November when temperatures drop below 25°C. Avoid late planting after mid-December.",
                "weather_aware_harvest_timing": "Harvest in March before summer heat intensifies. High temperatures can reduce grain quality.",
                "weather_alerts": [
                    {
                        "alert_type": "cold_wave",
                        "severity": "low",
                        "description": "Cold wave possible in January",
                        "action": "Light irrigation during cold periods can protect crop",
                    }
                ],
            },
            "zaid": {
                "recommended_crop": "Green Gram (Moong)",
                "expected_profit_per_acre": 15000,
                "seasonal_weather_pattern": "Hot summer months with high evaporation. Requires short-duration crops.",
                "weather_aware_planting_timing": "Plant immediately after Rabi harvest in April to utilize residual moisture.",
                "weather_aware_harvest_timing": "Harvest before monsoon onset in June to prevent pod damage.",
                "weather_alerts": [
                    {
                        "alert_type": "heat_wave",
                        "severity": "high",
                        "description": "Severe heat waves common in May",
                        "action": "Maintain soil moisture and harvest early in the day",
                    }
                ],
            },
            "annual_summary": {
                "total_expected_profit_per_acre": 75000,
                "total_investment_per_acre": 27000,
                "roi_percentage": 178,
                "risk_level": "medium",
                "sustainability_score": 0.7,
            },
            "alternative_options": [],
            "monthly_action_plan": [],
        }


# Singleton instance
bedrock_service = BedrockService()
