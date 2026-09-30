"""
Supply Request Matching Service
Handles AI-powered matching of buyer supply requests with farmer listings using pgvector similarity search

Task 36.2 Enhancements:
- pgvector similarity search for efficient matching based on embeddings
- Amazon Bedrock integration for:
  * Optional Titan Embeddings for higher quality vector representations
  * AI-enhanced match reasoning with logistics insights
- Intelligent matching algorithm considering:
  * Crop type match (30% weight) - via vector similarity
  * Quality match (20% weight) - grade alignment
  * Quantity match (20% weight) - availability vs need
  * Location proximity (20% weight) - GPS distance or district match
  * Timing alignment (10% weight) - harvest vs delivery window
- Match scores (0-100) with component breakdowns
- Caching for embeddings to reduce API costs
- Graceful fallback from Bedrock to sentence-transformers
"""

import hashlib
import json
import logging
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional

from app.core.cache import get_cache_manager
from app.orm.marketplace_listing import MarketplaceListing
from app.orm.supply_match import SupplyMatch
from app.orm.supply_request import SupplyRequest
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)


class SupplyRequestMatchingService:
    """Service for matching supply requests with available farmer listings using pgvector"""

    def __init__(self, use_bedrock_embeddings: bool = True):
        self.bedrock_service = BedrockService()
        # Dimensionality remains 384 for database consistency (Titan 1536 is reduced to 384)
        self.embedding_dimension = 384
        self.use_bedrock_embeddings = use_bedrock_embeddings

        # Matching weights (must sum to 100)
        self.weights = {
            "crop_match": 30,  # Crop type similarity
            "quality_match": 20,  # Quality grade match
            "quantity_match": 20,  # Quantity availability
            "location_proximity": 20,  # Distance between locations
            "timing_alignment": 10,  # Delivery timing match
        }

    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate a cache key for embedding based on relevant fields"""
        # Create a stable string representation of the data
        key_parts = [
            str(data.get("crop_type", "")),
            str(data.get("quality_requirements", "")),
            str(data.get("quality_grade", "")),
            str(data.get("quantity_needed", data.get("estimated_quantity", 0))),
            str(data.get("delivery_state", data.get("location_state", ""))),
            str(data.get("delivery_district", data.get("location_district", ""))),
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _generate_request_embedding(self, supply_request: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a supply request
        Combines crop type, quality requirements, quantity, and location
        Uses Bedrock Titan Embeddings (Cloud-based, replaces local ML)
        """
        # Build text representation
        text_parts = [
            f"crop:{supply_request.get('crop_type', 'unknown')}",
            f"quality:{supply_request.get('quality_requirements', 'standard')}",
            f"quantity:{supply_request.get('quantity_needed', 0)}kg",
            f"location:{supply_request.get('delivery_state', '')}-{supply_request.get('delivery_district', '')}",
            f"emergency:{supply_request.get('is_emergency', False)}",
        ]

        text = " ".join(text_parts)

        # Use Bedrock embeddings exclusively
        embedding = self.bedrock_service.generate_embedding(text, reduce_to_384=True)
        return embedding

    def _generate_listing_embedding(self, listing: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a marketplace listing
        Combines crop type, quality grade, quantity, and location
        Uses Bedrock Titan Embeddings (Cloud-based, replaces local ML)
        """
        # Build text representation
        text_parts = [
            f"crop:{listing.get('crop_type', 'unknown')}",
            f"variety:{listing.get('crop_variety', '')}",
            f"quality:{listing.get('quality_grade', 'B')}",
            f"quantity:{listing.get('available_quantity', listing.get('estimated_quantity', 0))}kg",
            f"location:{listing.get('location_state', '')}-{listing.get('location_district', '')}",
        ]

        text = " ".join(text_parts)

        # Use Bedrock embeddings exclusively
        embedding = self.bedrock_service.generate_embedding(text, reduce_to_384=True)
        return embedding

    # Redundant local Bedrock methods removed. Centralized logic now in BedrockService.

    def _get_or_generate_embedding(
        self, data: Dict[str, Any], is_request: bool = True
    ) -> List[float]:
        """
        Get cached embedding or generate new one

        Args:
            data: Supply request or listing data
            is_request: True for supply request, False for listing

        Returns:
            Embedding vector
        """
        # Check if embedding already exists in data
        if data.get("embedding"):
            return data["embedding"]

        # Generate cache key
        cache_key = self._generate_cache_key(data)

        # Check if cache key matches stored one
        if data.get("embedding_cache_key") == cache_key and data.get("embedding"):
            return data["embedding"]

        # Check Redis cache
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled:
            redis_key = f"embedding:{'request' if is_request else 'listing'}:{cache_key}"
            cached_embedding = cache_manager.get(redis_key)
            if cached_embedding:
                logger.info(f"Cache hit for embedding: {redis_key}")
                return cached_embedding

        # Generate new embedding
        if is_request:
            embedding = self._generate_request_embedding(data)
        else:
            embedding = self._generate_listing_embedding(data)

        # Cache the embedding (24 hour TTL)
        if cache_manager and cache_manager.enabled:
            redis_key = f"embedding:{'request' if is_request else 'listing'}:{cache_key}"
            cache_manager.set(redis_key, embedding, 86400)  # 24 hours
            logger.info(f"Cached embedding: {redis_key}")

        # Update database with embedding and cache key
        model = SupplyRequest() if is_request else MarketplaceListing()
        model.update(data["id"], {"embedding": embedding, "embedding_cache_key": cache_key})

        return embedding

    def _call_bedrock_for_matching(self, prompt: str) -> str:
        """
        Call Bedrock AI for supply matching
        Uses the _invoke_claude method from BedrockService
        """
        try:
            return self.bedrock_service._invoke_claude(
                prompt=prompt, max_tokens=2000, temperature=0.3, use_instant=False
            )
        except Exception as e:
            logger.error(f"Bedrock API call failed: {str(e)}")
            raise

    def create_supply_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new supply request and find initial matches

        Args:
            data: Supply request data including buyer_id, crop_type, quantity, etc.

        Returns:
            Dict with request_id and initial_matches
        """
        # Create the supply request
        request = SupplyRequest()
        request_id = request.insert(data)

        # Get the created request to generate embedding
        supply_request = request.find(request_id)

        # Generate and store embedding
        embedding = self._get_or_generate_embedding(supply_request, is_request=True)

        # Find initial matches using pgvector
        matches = self.find_matches(request_id)

        return {
            "request_id": request_id,
            "initial_matches": matches,
            "status": "open",
            "matching_method": "pgvector_similarity_search",
        }

    def find_matches(self, request_id: int) -> Dict[str, Any]:
        """
        Find matching farmer listings for a supply request using pgvector similarity search

        Args:
            request_id: ID of the supply request

        Returns:
            Dict with single_farmer_matches and aggregated_options
        """
        # Get the supply request
        request = SupplyRequest()
        supply_request = request.find(request_id)

        if not supply_request:
            raise ValueError(f"Supply request {request_id} not found")

        # Use pgvector for initial similarity-based filtering
        similar_listings = self._find_matches_with_pgvector(
            supply_request, similarity_threshold=0.6, limit=20
        )

        if not similar_listings:
            return {
                "single_farmer_matches": [],
                "aggregated_options": [],
                "message": "No available listings found for this crop type",
            }

        # Calculate detailed match scores for each listing
        single_matches = []
        aggregation_candidates = []

        quantity_needed = float(supply_request.get("quantity_needed", 0))

        for listing in similar_listings:
            # Ensure listing has embedding
            if not listing.get("embedding"):
                listing_embedding = self._get_or_generate_embedding(listing, is_request=False)
                listing["embedding"] = listing_embedding

            # Calculate comprehensive match score
            vector_similarity = listing.get("similarity_score", 0.7)
            match_scores = self._calculate_match_score(supply_request, listing, vector_similarity)

            # Generate match reasoning
            reasoning = self._generate_match_reasoning(supply_request, listing, match_scores)

            quantity_available = float(
                listing.get("available_quantity", listing.get("estimated_quantity", 0))
            )

            match_data = {
                "listing_id": listing.get("id"),
                "farmer_id": listing.get("farmer_id"),
                "match_score": match_scores["overall_score"],
                "matched_quantity": min(quantity_available, quantity_needed),
                "price_offered": listing.get("price_per_unit", 0),
                "explanation": reasoning,
                "component_scores": match_scores["component_scores"],
                "distance_km": match_scores.get("distance_km"),
            }

            # Categorize as single match or aggregation candidate
            if quantity_available >= quantity_needed and match_scores["overall_score"] >= 60:
                single_matches.append(match_data)
            elif match_scores["overall_score"] >= 50:
                aggregation_candidates.append(match_data)

        # Sort single matches by score
        single_matches.sort(key=lambda x: x["match_score"], reverse=True)

        # Create aggregated options if needed
        aggregated_options = []
        if len(single_matches) < 3 and aggregation_candidates:
            aggregated_options = self._create_aggregated_options(
                supply_request, aggregation_candidates, quantity_needed
            )

        # Save matches to database
        matches_to_save = {
            "single_farmer_matches": single_matches[:10],  # Top 10
            "aggregated_options": aggregated_options[:5],  # Top 5
            "recommendation": self._generate_recommendation(single_matches, aggregated_options),
        }
        self._save_matches(request_id, matches_to_save)

        return matches_to_save

    def _create_aggregated_options(
        self,
        supply_request: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        quantity_needed: float,
    ) -> List[Dict[str, Any]]:
        """
        Create multi-farmer aggregation options to fulfill large orders

        Args:
            supply_request: The supply request
            candidates: List of candidate listings
            quantity_needed: Total quantity needed

        Returns:
            List of aggregated fulfillment options
        """
        # Sort candidates by match score
        candidates.sort(key=lambda x: x["match_score"], reverse=True)

        aggregated_options = []

        # Strategy 1: Best matches combination
        option1_farmers = []
        option1_quantity = 0
        option1_total_price = 0

        for candidate in candidates:
            if option1_quantity >= quantity_needed:
                break

            quantity_to_take = min(
                candidate["matched_quantity"], quantity_needed - option1_quantity
            )

            option1_farmers.append(
                {
                    "listing_id": candidate["listing_id"],
                    "farmer_id": candidate["farmer_id"],
                    "quantity": quantity_to_take,
                    "price": candidate["price_offered"],
                    "match_score": candidate["match_score"],
                }
            )

            option1_quantity += quantity_to_take
            option1_total_price += quantity_to_take * candidate["price_offered"]

        if option1_farmers and option1_quantity >= quantity_needed * 0.8:
            avg_score = sum(f["match_score"] for f in option1_farmers) / len(option1_farmers)
            aggregated_options.append(
                {
                    "farmers": option1_farmers,
                    "total_quantity": option1_quantity,
                    "average_price": (
                        round(option1_total_price / option1_quantity, 2)
                        if option1_quantity > 0
                        else 0
                    ),
                    "match_score": round(avg_score, 2),
                    "explanation": f"Combining {len(option1_farmers)} top-rated farmers to meet {option1_quantity:.0f}kg requirement",
                }
            )

        # Strategy 2: Location-optimized (same district preference)
        same_district_candidates = [
            c
            for c in candidates
            if c.get("component_scores", {}).get("location_proximity", 0) >= 90
        ]

        if len(same_district_candidates) >= 2:
            option2_farmers = []
            option2_quantity = 0
            option2_total_price = 0

            for candidate in same_district_candidates:
                if option2_quantity >= quantity_needed:
                    break

                quantity_to_take = min(
                    candidate["matched_quantity"], quantity_needed - option2_quantity
                )

                option2_farmers.append(
                    {
                        "listing_id": candidate["listing_id"],
                        "farmer_id": candidate["farmer_id"],
                        "quantity": quantity_to_take,
                        "price": candidate["price_offered"],
                        "match_score": candidate["match_score"],
                    }
                )

                option2_quantity += quantity_to_take
                option2_total_price += quantity_to_take * candidate["price_offered"]

            if option2_farmers and option2_quantity >= quantity_needed * 0.8:
                avg_score = sum(f["match_score"] for f in option2_farmers) / len(option2_farmers)
                aggregated_options.append(
                    {
                        "farmers": option2_farmers,
                        "total_quantity": option2_quantity,
                        "average_price": (
                            round(option2_total_price / option2_quantity, 2)
                            if option2_quantity > 0
                            else 0
                        ),
                        "match_score": round(avg_score, 2),
                        "explanation": f"Location-optimized: {len(option2_farmers)} farmers from same district for easier coordination",
                    }
                )

        return aggregated_options

    def _generate_recommendation(
        self, single_matches: List[Dict[str, Any]], aggregated_options: List[Dict[str, Any]]
    ) -> str:
        """Generate overall recommendation based on available matches"""
        if not single_matches and not aggregated_options:
            return "No suitable matches found. Consider adjusting requirements or expanding search area."

        if single_matches and single_matches[0]["match_score"] >= 80:
            return f"Excellent match found! Farmer {single_matches[0]['farmer_id']} can fulfill your entire order with {single_matches[0]['match_score']:.0f}% match score."

        if single_matches:
            return f"Found {len(single_matches)} single-farmer options. Top match has {single_matches[0]['match_score']:.0f}% compatibility."

        if aggregated_options:
            return f"No single farmer can fulfill entire order. {len(aggregated_options)} multi-farmer coordination options available."

        return "Matches found using intelligent pgvector similarity search."

    def _calculate_distance(
        self,
        lat1: Optional[float],
        lon1: Optional[float],
        lat2: Optional[float],
        lon2: Optional[float],
    ) -> Optional[float]:
        """
        Calculate distance between two GPS coordinates using Haversine formula
        Returns distance in kilometers, or None if coordinates missing
        """
        if not all([lat1, lon1, lat2, lon2]):
            return None

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r

    def _calculate_match_score(
        self, supply_request: Dict[str, Any], listing: Dict[str, Any], vector_similarity: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score based on multiple weighted factors

        Weights:
        - Crop match (30%): Based on vector similarity
        - Quality match (20%): Quality grade alignment
        - Quantity match (20%): Availability vs need
        - Location proximity (20%): Distance between locations
        - Timing alignment (10%): Delivery date match

        Returns:
            Dict with overall score (0-100) and component scores
        """
        scores = {}

        # 1. Crop Match (30%) - Use vector similarity
        scores["crop_match"] = vector_similarity * 100

        # 2. Quality Match (20%)
        quality_req = supply_request.get("quality_requirements", "").lower()
        quality_grade = listing.get("quality_grade", "B")

        # Quality grade mapping: A > B > C
        quality_map = {"a": 3, "b": 2, "c": 1}

        if "grade a" in quality_req or "premium" in quality_req:
            required_grade = 3
        elif "grade b" in quality_req or "standard" in quality_req:
            required_grade = 2
        else:
            required_grade = 1

        listing_grade = quality_map.get(quality_grade.lower(), 2)

        if listing_grade >= required_grade:
            scores["quality_match"] = 100
        elif listing_grade == required_grade - 1:
            scores["quality_match"] = 70
        else:
            scores["quality_match"] = 40

        # 3. Quantity Match (20%)
        quantity_needed = float(supply_request.get("quantity_needed", 0))
        quantity_available = float(
            listing.get("available_quantity", listing.get("estimated_quantity", 0))
        )

        if quantity_available >= quantity_needed:
            # Can fulfill entire order
            scores["quantity_match"] = 100
        elif quantity_available >= quantity_needed * 0.7:
            # Can fulfill 70%+ of order
            scores["quantity_match"] = 80
        elif quantity_available >= quantity_needed * 0.5:
            # Can fulfill 50%+ of order
            scores["quantity_match"] = 60
        else:
            # Less than 50% fulfillment
            scores["quantity_match"] = (quantity_available / quantity_needed) * 100

        # 4. Location Proximity (20%)
        # Try GPS-based distance first, fallback to district match
        distance_km = self._calculate_distance(
            supply_request.get("delivery_latitude"),
            supply_request.get("delivery_longitude"),
            listing.get("delivery_latitude"),
            listing.get("delivery_longitude"),
        )

        if distance_km is not None:
            # GPS-based scoring
            if distance_km <= 50:
                scores["location_proximity"] = 100
            elif distance_km <= 100:
                scores["location_proximity"] = 90
            elif distance_km <= 200:
                scores["location_proximity"] = 75
            elif distance_km <= 500:
                scores["location_proximity"] = 50
            else:
                scores["location_proximity"] = 30
        else:
            # Fallback to district/state match
            req_state = supply_request.get("delivery_state", "").lower()
            req_district = supply_request.get("delivery_district", "").lower()
            list_state = listing.get("location_state", "").lower()
            list_district = listing.get("location_district", "").lower()

            if req_district == list_district:
                scores["location_proximity"] = 100
            elif req_state == list_state:
                scores["location_proximity"] = 70
            else:
                scores["location_proximity"] = 40

        # 5. Timing Alignment (10%)
        from datetime import datetime, timedelta

        try:
            delivery_start = supply_request.get("delivery_date_start")
            delivery_end = supply_request.get("delivery_date_end")
            harvest_date = listing.get("expected_harvest_date")

            if isinstance(delivery_start, str):
                delivery_start = datetime.fromisoformat(delivery_start.replace("Z", "+00:00"))
            if isinstance(delivery_end, str):
                delivery_end = datetime.fromisoformat(delivery_end.replace("Z", "+00:00"))
            if isinstance(harvest_date, str):
                harvest_date = datetime.fromisoformat(harvest_date.replace("Z", "+00:00"))

            if harvest_date and delivery_start and delivery_end:
                # Check if harvest date falls within delivery window
                if delivery_start <= harvest_date <= delivery_end:
                    scores["timing_alignment"] = 100
                else:
                    # Calculate days difference
                    if harvest_date < delivery_start:
                        days_diff = (delivery_start - harvest_date).days
                    else:
                        days_diff = (harvest_date - delivery_end).days

                    # Score based on days difference
                    if days_diff <= 7:
                        scores["timing_alignment"] = 90
                    elif days_diff <= 14:
                        scores["timing_alignment"] = 75
                    elif days_diff <= 30:
                        scores["timing_alignment"] = 50
                    else:
                        scores["timing_alignment"] = 30
            else:
                scores["timing_alignment"] = 50  # Neutral if dates missing
        except Exception as e:
            logger.warning(f"Error calculating timing alignment: {e}")
            scores["timing_alignment"] = 50

        # Calculate weighted overall score
        overall_score = (
            scores["crop_match"] * self.weights["crop_match"] / 100
            + scores["quality_match"] * self.weights["quality_match"] / 100
            + scores["quantity_match"] * self.weights["quantity_match"] / 100
            + scores["location_proximity"] * self.weights["location_proximity"] / 100
            + scores["timing_alignment"] * self.weights["timing_alignment"] / 100
        )

        return {
            "overall_score": round(overall_score, 2),
            "component_scores": scores,
            "distance_km": distance_km,
        }

    def _generate_match_reasoning(
        self, supply_request: Dict[str, Any], listing: Dict[str, Any], match_scores: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation for the match using Bedrock AI"""
        reasons = []
        scores = match_scores["component_scores"]

        # Crop match
        if scores["crop_match"] >= 80:
            reasons.append(f"Excellent crop match ({scores['crop_match']:.0f}%)")
        elif scores["crop_match"] >= 60:
            reasons.append(f"Good crop match ({scores['crop_match']:.0f}%)")

        # Quality
        if scores["quality_match"] >= 90:
            reasons.append(f"Quality grade {listing.get('quality_grade', 'B')} meets requirements")

        # Quantity
        quantity_available = float(
            listing.get("available_quantity", listing.get("estimated_quantity", 0))
        )
        quantity_needed = float(supply_request.get("quantity_needed", 0))
        if quantity_available >= quantity_needed:
            reasons.append(f"Can fulfill entire order ({quantity_available:.0f}kg available)")
        else:
            reasons.append(
                f"Partial fulfillment ({quantity_available:.0f}kg of {quantity_needed:.0f}kg needed)"
            )

        # Location
        distance_km = match_scores.get("distance_km")
        if distance_km:
            reasons.append(f"Distance: {distance_km:.0f}km")
        elif scores["location_proximity"] >= 90:
            reasons.append("Same district delivery")

        # Timing
        if scores["timing_alignment"] >= 90:
            reasons.append("Harvest timing aligns with delivery window")

        reasoning = "; ".join(reasons)

        # Use Bedrock to enhance reasoning if match score is high enough
        if match_scores["overall_score"] >= 70:
            try:
                enhanced_reasoning = self._enhance_reasoning_with_bedrock(
                    supply_request, listing, match_scores, reasoning
                )
                return enhanced_reasoning
            except Exception as e:
                logger.warning(f"Failed to enhance reasoning with Bedrock: {e}")
                return reasoning

        return reasoning

    def _enhance_reasoning_with_bedrock(
        self,
        supply_request: Dict[str, Any],
        listing: Dict[str, Any],
        match_scores: Dict[str, Any],
        basic_reasoning: str,
    ) -> str:
        """
        Use Bedrock to generate enhanced match reasoning with logistics insights

        Args:
            supply_request: The buyer's supply request
            listing: The matched farmer listing
            match_scores: Calculated match scores
            basic_reasoning: Basic reasoning string

        Returns:
            Enhanced reasoning with AI insights
        """
        prompt = f"""You are an agricultural supply chain expert. Provide a concise, actionable explanation for why this farmer-buyer match is good.

Buyer Requirements:
- Crop: {supply_request.get('crop_type')}
- Quantity: {supply_request.get('quantity_needed')}kg
- Quality: {supply_request.get('quality_requirements', 'Standard')}
- Delivery: {supply_request.get('delivery_district')}, {supply_request.get('delivery_state')}
- Timing: {supply_request.get('delivery_date_start')} to {supply_request.get('delivery_date_end')}

Farmer Offering:
- Crop: {listing.get('crop_type')} ({listing.get('crop_variety', 'standard variety')})
- Quantity: {listing.get('available_quantity', listing.get('estimated_quantity'))}kg
- Quality: Grade {listing.get('quality_grade', 'B')}
- Location: {listing.get('location_district')}, {listing.get('location_state')}
- Harvest: {listing.get('expected_harvest_date')}
- Price: ₹{listing.get('price_per_unit', 0)}/kg

Match Scores:
- Overall: {match_scores['overall_score']:.0f}%
- Crop Match: {match_scores['component_scores']['crop_match']:.0f}%
- Quality Match: {match_scores['component_scores']['quality_match']:.0f}%
- Quantity Match: {match_scores['component_scores']['quantity_match']:.0f}%
- Location: {match_scores['component_scores']['location_proximity']:.0f}%
- Timing: {match_scores['component_scores']['timing_alignment']:.0f}%

Basic Analysis: {basic_reasoning}

Provide a 2-3 sentence explanation that:
1. Highlights the strongest match factors
2. Mentions any logistics considerations (distance, timing, coordination)
3. Gives actionable next steps for the buyer

Keep it concise and practical. Focus on why this match makes business sense."""

        try:
            response = self.bedrock_service._invoke_claude(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
                use_instant=True,  # Use instant for faster response
            )

            # Clean up the response
            enhanced = response.strip()

            # If response is too long, truncate
            if len(enhanced) > 500:
                enhanced = enhanced[:497] + "..."

            return enhanced

        except Exception as e:
            logger.error(f"Bedrock reasoning enhancement failed: {e}")
            raise

    def _find_matches_with_pgvector(
        self, supply_request: Dict[str, Any], similarity_threshold: float = 0.6, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find matching listings using pgvector similarity search

        Args:
            supply_request: The supply request data
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum number of matches to return

        Returns:
            List of matched listings with similarity scores
        """
        # Generate or get embedding for supply request
        request_embedding = self._get_or_generate_embedding(supply_request, is_request=True)

        # Build SQL query for vector similarity search
        # Using cosine distance operator <=> from pgvector
        from sqlalchemy import text

        from app.core.database import get_db_context

        # Convert embedding list to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, request_embedding)) + "]"

        query = text("""
            SELECT 
                ml.id,
                ml.farm_id,
                ml.farmer_id,
                ml.crop_type,
                ml.crop_variety,
                ml.expected_harvest_date,
                ml.estimated_quantity,
                ml.available_quantity,
                ml.quality_grade,
                ml.location_state,
                ml.location_district,
                ml.farmer_contact_phone,
                ml.farmer_contact_email,
                ml.status,
                ml.delivery_latitude,
                ml.delivery_longitude,
                ml.delivery_pincode,
                ml.delivery_village,
                ml.delivery_address_line,
                ml.price_per_unit,
                ml.embedding_cache_key,
                ml.created_at,
                ml.updated_at,
                1 - (ml.embedding <=> :query_vector::vector) as similarity_score
            FROM marketplace_listings ml
            WHERE 
                ml.crop_type = :crop_type
                AND ml.status = 'active'
                AND ml.embedding IS NOT NULL
                AND 1 - (ml.embedding <=> :query_vector::vector) > :threshold
            ORDER BY ml.embedding <=> :query_vector::vector
            LIMIT :limit
        """)

        # Execute query
        try:
            # Get database session using context manager
            with get_db_context() as db:
                results = db.execute(
                    query,
                    {
                        "query_vector": embedding_str,
                        "crop_type": supply_request.get("crop_type"),
                        "threshold": similarity_threshold,
                        "limit": limit,
                    },
                )

                matches = []
                for row in results:
                    listing_dict = dict(row._mapping)
                    # Remove embedding from result to reduce memory usage
                    listing_dict.pop("embedding", None)
                    matches.append(listing_dict)

            logger.info(f"Found {len(matches)} matches using pgvector similarity search")
            return matches

        except Exception as e:
            logger.error(f"Error in pgvector similarity search: {e}")
            logger.exception(e)
            # Fallback to basic query without vector search
            return self._get_available_listings(supply_request["crop_type"])

    def _get_available_listings(self, crop_type: str) -> List[Dict[str, Any]]:
        """
        Get all available marketplace listings for a specific crop type

        Args:
            crop_type: Type of crop to search for

        Returns:
            List of available listings
        """
        listing = MarketplaceListing()

        # Query for active listings with the specified crop type
        # Status should be 'active' or 'available'
        listings = listing.where("crop_type", crop_type).where("status", "active").get()

        return listings if listings else []

    def _ai_match_supply_to_demand(
        self, supply_request: Dict[str, Any], available_listings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Amazon Bedrock to intelligently match supply with demand

        Args:
            supply_request: The buyer's supply request
            available_listings: Available farmer listings

        Returns:
            Dict with single_farmer_matches and aggregated_options
        """
        # Format listings for the prompt
        listings_text = self._format_listings_for_prompt(available_listings)

        # Build the Bedrock prompt
        prompt = f"""
You are an agricultural supply chain expert. Match buyer requirements with available farmer supplies.

Buyer Requirements:
- Crop Type: {supply_request.get('crop_type', 'N/A')}
- Quantity Needed: {supply_request.get('quantity_needed', 0)} kg
- Quality Requirements: {supply_request.get('quality_requirements', 'Standard quality')}
- Delivery Window: {supply_request.get('delivery_date_start', 'N/A')} to {supply_request.get('delivery_date_end', 'N/A')}
- Max Price: ₹{supply_request.get('max_price_per_unit', 'Not specified')}/kg
- Emergency Request: {'Yes' if supply_request.get('is_emergency', False) else 'No'}
- Delivery Location: {supply_request.get('delivery_district', 'N/A')}, {supply_request.get('delivery_state', 'N/A')}

Available Farmer Supplies:
{listings_text}

Please analyze and provide:
1. Best single-farmer matches (farmers who can fulfill the entire order alone)
2. Multi-farmer aggregation options (combining multiple farmers to meet the requirement)
3. Match scores (0-100) for each option based on:
   - Quality match
   - Price competitiveness
   - Location proximity
   - Delivery timing alignment
   - Farmer reliability
4. Recommended approach and logistics considerations

Format your response as JSON with this structure:
{{
  "single_farmer_matches": [
    {{
      "listing_id": <id>,
      "farmer_id": <id>,
      "match_score": <0-100>,
      "matched_quantity": <kg>,
      "price_offered": <price>,
      "explanation": "<why this is a good match>"
    }}
  ],
  "aggregated_options": [
    {{
      "farmers": [
        {{
          "listing_id": <id>,
          "farmer_id": <id>,
          "quantity": <kg>,
          "price": <price>
        }}
      ],
      "total_quantity": <kg>,
      "average_price": <price>,
      "match_score": <0-100>,
      "explanation": "<coordination strategy>"
    }}
  ],
  "recommendation": "<overall recommendation>"
}}
"""

        try:
            # Call Bedrock for AI matching
            response = self._call_bedrock_for_matching(prompt)

            # Parse the JSON response
            matches = self._parse_bedrock_response(response)

            return matches

        except Exception as e:
            print(f"Error in AI matching: {str(e)}")
            # Fallback to simple matching if AI fails
            return self._simple_match_fallback(supply_request, available_listings)

    def _format_listings_for_prompt(self, listings: List[Dict[str, Any]]) -> str:
        """Format listings for the Bedrock prompt"""
        formatted = []
        for i, listing in enumerate(listings, 1):
            formatted.append(f"""
Listing {i}:
- ID: {listing.get('id')}
- Farmer ID: {listing.get('farmer_id')}
- Quantity Available: {listing.get('quantity_available', 0)} kg
- Quality Grade: {listing.get('quality_grade', 'N/A')}
- Price: ₹{listing.get('price_per_unit', 0)}/kg
- Harvest Date: {listing.get('expected_harvest_date', 'N/A')}
- Location: {listing.get('district', 'N/A')}, {listing.get('state', 'N/A')}
""")
        return "\n".join(formatted)

    def _parse_bedrock_response(self, response: str) -> Dict[str, Any]:
        """Parse Bedrock JSON response"""
        try:
            # Try to extract JSON from the response
            # Bedrock might wrap JSON in markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            matches = json.loads(json_str)
            return matches

        except json.JSONDecodeError as e:
            print(f"Failed to parse Bedrock response as JSON: {str(e)}")
            print(f"Response: {response}")
            return {
                "single_farmer_matches": [],
                "aggregated_options": [],
                "recommendation": "Unable to parse AI response",
            }

    def _simple_match_fallback(
        self, supply_request: Dict[str, Any], available_listings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simple fallback matching when AI is unavailable
        Matches based on quantity and price
        """
        quantity_needed = float(supply_request.get("quantity_needed", 0))
        max_price = float(supply_request.get("max_price_per_unit", float("inf")))

        single_matches = []
        aggregation_candidates = []

        for listing in available_listings:
            quantity_available = float(listing.get("quantity_available", 0))
            price = float(listing.get("price_per_unit", 0))

            # Skip if price is too high
            if max_price and price > max_price:
                continue

            # Calculate match score (simple version)
            quantity_match = min(quantity_available / quantity_needed, 1.0) * 50
            price_match = (1 - min(price / max_price, 1.0)) * 50 if max_price else 25
            match_score = quantity_match + price_match

            match_data = {
                "listing_id": listing.get("id"),
                "farmer_id": listing.get("farmer_id"),
                "match_score": round(match_score, 2),
                "matched_quantity": min(quantity_available, quantity_needed),
                "price_offered": price,
                "explanation": f"Quantity match: {round(quantity_match, 1)}%, Price match: {round(price_match, 1)}%",
            }

            # If farmer can fulfill entire order, add to single matches
            if quantity_available >= quantity_needed:
                single_matches.append(match_data)
            else:
                aggregation_candidates.append(match_data)

        # Sort by match score
        single_matches.sort(key=lambda x: x["match_score"], reverse=True)

        # Create aggregated options if no single farmer can fulfill
        aggregated_options = []
        if not single_matches and aggregation_candidates:
            # Simple aggregation: combine top candidates
            aggregation_candidates.sort(key=lambda x: x["match_score"], reverse=True)

            total_quantity = 0
            farmers = []
            total_price = 0

            for candidate in aggregation_candidates:
                if total_quantity >= quantity_needed:
                    break

                quantity_to_take = min(
                    candidate["matched_quantity"], quantity_needed - total_quantity
                )

                farmers.append(
                    {
                        "listing_id": candidate["listing_id"],
                        "farmer_id": candidate["farmer_id"],
                        "quantity": quantity_to_take,
                        "price": candidate["price_offered"],
                    }
                )

                total_quantity += quantity_to_take
                total_price += quantity_to_take * candidate["price_offered"]

            if farmers:
                aggregated_options.append(
                    {
                        "farmers": farmers,
                        "total_quantity": total_quantity,
                        "average_price": (
                            round(total_price / total_quantity, 2) if total_quantity > 0 else 0
                        ),
                        "match_score": 70,  # Default score for aggregated
                        "explanation": f"Combining {len(farmers)} farmers to meet requirement",
                    }
                )

        return {
            "single_farmer_matches": single_matches[:5],  # Top 5
            "aggregated_options": aggregated_options[:3],  # Top 3
            "recommendation": "Matches found using simple algorithm (AI unavailable)",
        }

    def _save_matches(self, request_id: int, matches: Dict[str, Any]) -> None:
        """Save matches to the database"""
        match_model = SupplyMatch()

        # Save single farmer matches
        for match in matches.get("single_farmer_matches", []):
            match_data = {
                "request_id": request_id,
                "listing_id": match.get("listing_id"),
                "farmer_id": match.get("farmer_id"),
                "matched_quantity": match.get("matched_quantity"),
                "match_score": match.get("match_score"),
                "price_offered": match.get("price_offered"),
                "status": "suggested",
                "match_explanation": match.get("explanation"),
                "is_aggregated": False,
            }
            match_model.insert(match_data)

        # Save aggregated options
        for i, option in enumerate(matches.get("aggregated_options", [])):
            group_id = f"agg_{request_id}_{i}"

            for farmer in option.get("farmers", []):
                match_data = {
                    "request_id": request_id,
                    "listing_id": farmer.get("listing_id"),
                    "farmer_id": farmer.get("farmer_id"),
                    "matched_quantity": farmer.get("quantity"),
                    "match_score": option.get("match_score"),
                    "price_offered": farmer.get("price"),
                    "status": "suggested",
                    "match_explanation": option.get("explanation"),
                    "is_aggregated": True,
                    "aggregation_group_id": group_id,
                }
                match_model.insert(match_data)

    def get_matches_for_request(self, request_id: int) -> Dict[str, Any]:
        """
        Get all matches for a supply request

        Args:
            request_id: ID of the supply request

        Returns:
            Dict with single_farmer_matches and aggregated_options
        """
        match_model = SupplyMatch()

        # Get all matches for this request
        all_matches = match_model.where("request_id", request_id).get()

        if not all_matches:
            return {"single_farmer_matches": [], "aggregated_options": []}

        # Separate single and aggregated matches
        single_matches = []
        aggregated_groups = {}

        for match in all_matches:
            if not match.get("is_aggregated"):
                single_matches.append(match)
            else:
                group_id = match.get("aggregation_group_id")
                if group_id not in aggregated_groups:
                    aggregated_groups[group_id] = []
                aggregated_groups[group_id].append(match)

        # Format aggregated options
        aggregated_options = []
        for group_id, farmers in aggregated_groups.items():
            total_quantity = sum(f.get("matched_quantity", 0) for f in farmers)
            total_price = sum(
                f.get("matched_quantity", 0) * f.get("price_offered", 0) for f in farmers
            )

            aggregated_options.append(
                {
                    "group_id": group_id,
                    "farmers": farmers,
                    "total_quantity": total_quantity,
                    "average_price": (
                        round(total_price / total_quantity, 2) if total_quantity > 0 else 0
                    ),
                    "match_score": farmers[0].get("match_score") if farmers else 0,
                    "explanation": farmers[0].get("match_explanation") if farmers else "",
                }
            )

        return {"single_farmer_matches": single_matches, "aggregated_options": aggregated_options}

    def accept_match(
        self,
        request_id: int,
        match_id: Optional[int] = None,
        aggregation_group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Accept a supply match and create booking(s)

        This method:
        1. Creates advance booking(s) for accepted match(es)
        2. Updates match status to 'accepted'
        3. Sends notifications to farmers about the match acceptance
        4. Updates supply request status
        5. Tracks buyer acceptance timestamp

        Args:
            request_id: ID of the supply request
            match_id: ID of single match to accept (optional)
            aggregation_group_id: ID of aggregated group to accept (optional)

        Returns:
            Dict with booking details and notification status
        """
        from app.orm.advance_booking import AdvanceBooking
        from app.services.notification_service import get_notification_service

        match_model = SupplyMatch()
        request_model = SupplyRequest()
        booking_model = AdvanceBooking()
        listing_model = MarketplaceListing()
        notification_service = get_notification_service()

        # Get the supply request
        supply_request = request_model.find(request_id)
        if not supply_request:
            raise ValueError(f"Supply request {request_id} not found")

        bookings = []
        notifications_sent = []
        acceptance_timestamp = datetime.now()

        if match_id:
            # Accept single farmer match
            match = match_model.find(match_id)
            if not match or match.get("request_id") != request_id:
                raise ValueError(f"Match {match_id} not found for request {request_id}")

            # Create booking
            booking_data = {
                "listing_id": match.get("listing_id"),
                "buyer_id": supply_request.get("buyer_id"),
                "farmer_id": match.get("farmer_id"),
                "quantity_booked": match.get("matched_quantity"),
                "price_per_unit": match.get("price_offered"),
                "total_amount": match.get("matched_quantity") * match.get("price_offered"),
                "expected_delivery_date": supply_request.get("delivery_date_end"),
                "status": "pending_farmer_confirmation",
                "booking_type": "supply_request",
                "supply_request_id": request_id,
            }
            booking_id = booking_model.insert(booking_data)
            bookings.append(booking_id)

            # Update match status with timestamps
            match_model.update(
                match_id,
                {
                    "status": "buyer_accepted",
                    "buyer_accepted_at": acceptance_timestamp,
                    "farmer_confirmation_status": "pending",
                },
            )

            # Send notification to farmer
            listing = listing_model.find(match.get("listing_id"))
            if listing:
                notification_result = self._notify_farmer_of_match_acceptance(
                    notification_service=notification_service,
                    farmer_id=match.get("farmer_id"),
                    listing=listing,
                    supply_request=supply_request,
                    matched_quantity=match.get("matched_quantity"),
                    price_offered=match.get("price_offered"),
                    booking_id=booking_id,
                    is_aggregated=False,
                )
                notifications_sent.append(notification_result)

        elif aggregation_group_id:
            # Accept aggregated match
            matches = (
                match_model.where("request_id", request_id)
                .where("aggregation_group_id", aggregation_group_id)
                .get()
            )

            if not matches:
                raise ValueError(f"Aggregation group {aggregation_group_id} not found")

            # Create booking for each farmer in the group
            for match in matches:
                booking_data = {
                    "listing_id": match.get("listing_id"),
                    "buyer_id": supply_request.get("buyer_id"),
                    "farmer_id": match.get("farmer_id"),
                    "quantity_booked": match.get("matched_quantity"),
                    "price_per_unit": match.get("price_offered"),
                    "total_amount": match.get("matched_quantity") * match.get("price_offered"),
                    "expected_delivery_date": supply_request.get("delivery_date_end"),
                    "status": "pending_farmer_confirmation",
                    "booking_type": "supply_request_aggregated",
                    "supply_request_id": request_id,
                    "aggregation_group_id": aggregation_group_id,
                }
                booking_id = booking_model.insert(booking_data)
                bookings.append(booking_id)

                # Update match status with timestamps
                match_model.update(
                    match.get("id"),
                    {
                        "status": "buyer_accepted",
                        "buyer_accepted_at": acceptance_timestamp,
                        "farmer_confirmation_status": "pending",
                    },
                )

                # Send notification to farmer
                listing = listing_model.find(match.get("listing_id"))
                if listing:
                    notification_result = self._notify_farmer_of_match_acceptance(
                        notification_service=notification_service,
                        farmer_id=match.get("farmer_id"),
                        listing=listing,
                        supply_request=supply_request,
                        matched_quantity=match.get("matched_quantity"),
                        price_offered=match.get("price_offered"),
                        booking_id=booking_id,
                        is_aggregated=True,
                        total_farmers=len(matches),
                    )
                    notifications_sent.append(notification_result)

        else:
            raise ValueError("Either match_id or aggregation_group_id must be provided")

        # Update supply request status
        if len(bookings) > 0:
            request_model.update(
                request_id, {"status": "matched", "updated_at": acceptance_timestamp}
            )

        return {
            "success": True,
            "booking_ids": bookings,
            "notifications_sent": len([n for n in notifications_sent if n.get("success")]),
            "message": f"Created {len(bookings)} booking(s) and notified {len(notifications_sent)} farmer(s)",
            "acceptance_timestamp": acceptance_timestamp.isoformat(),
            "awaiting_farmer_confirmation": True,
        }

    def _notify_farmer_of_match_acceptance(
        self,
        notification_service,
        farmer_id: int,
        listing: Dict[str, Any],
        supply_request: Dict[str, Any],
        matched_quantity: float,
        price_offered: float,
        booking_id: int,
        is_aggregated: bool = False,
        total_farmers: int = 1,
    ) -> Dict[str, Any]:
        """
        Send notification to farmer when buyer accepts a match

        Args:
            notification_service: NotificationService instance
            farmer_id: ID of the farmer
            listing: Marketplace listing data
            supply_request: Supply request data
            matched_quantity: Quantity matched
            price_offered: Price per unit
            booking_id: Created booking ID
            is_aggregated: Whether this is part of aggregated fulfillment
            total_farmers: Total farmers in aggregated group

        Returns:
            Notification result dictionary
        """
        from app.orm.user import User

        # Get farmer details
        user_model = User()
        farmer = user_model.find(farmer_id)

        if not farmer:
            logger.warning(f"Farmer {farmer_id} not found for notification")
            return {"success": False, "error": "Farmer not found"}

        # Prepare notification message
        farmer_name = farmer.get("name", "Farmer")
        farmer_phone = listing.get("farmer_contact_phone") or farmer.get("phone")
        farmer_email = listing.get("farmer_contact_email") or farmer.get("email")

        crop_type = supply_request.get("crop_type")
        total_amount = matched_quantity * price_offered

        # Build message
        if is_aggregated:
            subject = f"🎉 Supply Match Accepted - Multi-Farmer Order ({total_farmers} farmers)"
            message = f"""Hello {farmer_name},

Great news! A buyer has accepted your supply match as part of a coordinated multi-farmer order.

Match Details:
- Crop: {crop_type}
- Your Quantity: {matched_quantity:.2f} kg
- Price: ₹{price_offered:.2f}/kg
- Your Total: ₹{total_amount:,.2f}
- Booking ID: #{booking_id}
- Coordination: {total_farmers} farmers working together

Buyer Requirements:
- Total Needed: {supply_request.get('quantity_needed'):.2f} kg
- Quality: {supply_request.get('quality_requirements', 'Standard')}
- Delivery: {supply_request.get('delivery_date_start')} to {supply_request.get('delivery_date_end')}
- Location: {supply_request.get('delivery_district')}, {supply_request.get('delivery_state')}

IMPORTANT - Multi-Farmer Coordination:
✓ You are part of a group of {total_farmers} farmers
✓ Quality consistency is critical across all farmers
✓ Delivery timing must be coordinated
✓ Payment will be distributed based on your quantity

Next Steps:
1. Review and CONFIRM or REJECT this match within 24 hours
2. Coordinate with other farmers for consistent quality
3. Prepare for quality verification
4. Plan delivery logistics

Login to CropSense AI to confirm your participation and view coordination details."""
        else:
            subject = f"🎉 Supply Match Accepted - Direct Order"
            message = f"""Hello {farmer_name},

Excellent news! A buyer has accepted your supply match for a direct order.

Match Details:
- Crop: {crop_type}
- Quantity: {matched_quantity:.2f} kg
- Price: ₹{price_offered:.2f}/kg
- Total Amount: ₹{total_amount:,.2f}
- Booking ID: #{booking_id}

Buyer Requirements:
- Quality: {supply_request.get('quality_requirements', 'Standard')}
- Delivery: {supply_request.get('delivery_date_start')} to {supply_request.get('delivery_date_end')}
- Location: {supply_request.get('delivery_district')}, {supply_request.get('delivery_state')}

Next Steps:
1. Review and CONFIRM or REJECT this match within 24 hours
2. Prepare for quality verification
3. Plan delivery logistics
4. Track payment milestones

Login to CropSense AI to confirm your acceptance and view complete booking details."""

        # Send notification
        try:
            result = notification_service._send_notification(
                topic_arn=notification_service.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=farmer_phone,
                email=farmer_email,
                notification_type="supply_match_accepted",
                metadata={
                    "booking_id": booking_id,
                    "farmer_id": farmer_id,
                    "crop_type": crop_type,
                    "quantity": matched_quantity,
                    "is_aggregated": is_aggregated,
                    "total_farmers": total_farmers,
                },
            )

            logger.info(
                f"Match acceptance notification sent to farmer {farmer_id} for booking {booking_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to send match acceptance notification to farmer {farmer_id}: {e}")
            return {"success": False, "error": str(e), "notification_type": "supply_match_accepted"}

    def farmer_confirm_match(
        self, match_id: int, farmer_id: int, confirmation: bool, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Farmer confirms or rejects a match acceptance

        Args:
            match_id: ID of the match
            farmer_id: ID of the farmer (for verification)
            confirmation: True to accept, False to reject
            notes: Optional notes from farmer

        Returns:
            Dict with confirmation status and next steps
        """
        from app.orm.advance_booking import AdvanceBooking
        from app.services.notification_service import get_notification_service

        match_model = SupplyMatch()
        booking_model = AdvanceBooking()
        request_model = SupplyRequest()
        notification_service = get_notification_service()

        # Get the match
        match = match_model.find(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        # Verify farmer
        if match.get("farmer_id") != farmer_id:
            raise ValueError(f"Match {match_id} does not belong to farmer {farmer_id}")

        # Check if already confirmed/rejected
        if match.get("farmer_confirmation_status") in ["confirmed", "rejected"]:
            return {
                "success": False,
                "message": f"Match already {match.get('farmer_confirmation_status')}",
                "current_status": match.get("farmer_confirmation_status"),
            }

        confirmation_timestamp = datetime.now()

        if confirmation:
            # Farmer accepts the match
            match_model.update(
                match_id,
                {
                    "farmer_confirmation_status": "confirmed",
                    "farmer_confirmed_at": confirmation_timestamp,
                    "status": "confirmed",
                    "delivery_notes": notes,
                },
            )

            # Update booking status
            booking = (
                booking_model.where("listing_id", match.get("listing_id"))
                .where("farmer_id", farmer_id)
                .where("status", "pending_farmer_confirmation")
                .first()
            )

            if booking:
                booking_model.update(
                    booking.get("id"), {"status": "confirmed", "updated_at": confirmation_timestamp}
                )

                # Create payment milestones
                self._create_payment_milestones(booking.get("id"), booking)

            # Notify buyer of farmer confirmation
            supply_request = request_model.find(match.get("request_id"))
            if supply_request:
                self._notify_buyer_of_farmer_confirmation(
                    notification_service=notification_service,
                    buyer_id=supply_request.get("buyer_id"),
                    supply_request=supply_request,
                    match=match,
                    confirmed=True,
                    notes=notes,
                )

            # Check if all farmers in aggregated group have confirmed
            if match.get("is_aggregated"):
                self._check_aggregated_group_status(match.get("aggregation_group_id"))

            return {
                "success": True,
                "message": "Match confirmed successfully",
                "status": "confirmed",
                "confirmation_timestamp": confirmation_timestamp.isoformat(),
                "next_steps": [
                    "Prepare crop for quality verification",
                    "Coordinate delivery logistics",
                    "Track payment milestones",
                ],
            }
        else:
            # Farmer rejects the match
            match_model.update(
                match_id,
                {
                    "farmer_confirmation_status": "rejected",
                    "farmer_confirmed_at": confirmation_timestamp,
                    "status": "rejected",
                    "delivery_notes": notes,
                },
            )

            # Update booking status
            booking = (
                booking_model.where("listing_id", match.get("listing_id"))
                .where("farmer_id", farmer_id)
                .where("status", "pending_farmer_confirmation")
                .first()
            )

            if booking:
                booking_model.update(
                    booking.get("id"),
                    {
                        "status": "cancelled",
                        "cancellation_reason": notes or "Farmer rejected match",
                        "updated_at": confirmation_timestamp,
                    },
                )

            # Notify buyer of farmer rejection
            supply_request = request_model.find(match.get("request_id"))
            if supply_request:
                self._notify_buyer_of_farmer_confirmation(
                    notification_service=notification_service,
                    buyer_id=supply_request.get("buyer_id"),
                    supply_request=supply_request,
                    match=match,
                    confirmed=False,
                    notes=notes,
                )

                # If aggregated, check if we need to find replacement
                if match.get("is_aggregated"):
                    self._handle_aggregated_rejection(match)

            return {
                "success": True,
                "message": "Match rejected",
                "status": "rejected",
                "rejection_timestamp": confirmation_timestamp.isoformat(),
                "reason": notes,
            }

    def _create_payment_milestones(self, booking_id: int, booking: Dict[str, Any]) -> None:
        """
        Create payment milestones for a confirmed booking

        Standard milestones:
        - 30% advance payment (at booking confirmation)
        - 40% at quality verification
        - 30% at delivery

        Args:
            booking_id: ID of the booking
            booking: Booking data
        """
        from app.orm.payment_milestone import PaymentMilestone

        milestone_model = PaymentMilestone()
        total_amount = float(booking.get("total_amount", 0))
        expected_delivery = booking.get("expected_delivery_date")

        # Calculate milestone amounts
        advance_amount = total_amount * 0.30
        quality_amount = total_amount * 0.40
        delivery_amount = total_amount * 0.30

        # Calculate due dates
        from datetime import timedelta

        now = datetime.now()

        if isinstance(expected_delivery, str):
            expected_delivery = datetime.fromisoformat(expected_delivery.replace("Z", "+00:00"))

        quality_due = expected_delivery - timedelta(days=7)  # 7 days before delivery

        # Create milestones
        milestones = [
            {
                "booking_id": booking_id,
                "milestone_type": "advance_payment",
                "amount": advance_amount,
                "due_date": now + timedelta(days=3),  # 3 days to pay advance
                "status": "pending",
                "description": "30% advance payment at booking confirmation",
            },
            {
                "booking_id": booking_id,
                "milestone_type": "quality_verification",
                "amount": quality_amount,
                "due_date": quality_due,
                "status": "pending",
                "description": "40% payment after quality verification",
            },
            {
                "booking_id": booking_id,
                "milestone_type": "delivery",
                "amount": delivery_amount,
                "due_date": expected_delivery,
                "status": "pending",
                "description": "30% final payment at delivery",
            },
        ]

        for milestone_data in milestones:
            milestone_model.insert(milestone_data)

        logger.info(f"Created 3 payment milestones for booking {booking_id}")

    def _notify_buyer_of_farmer_confirmation(
        self,
        notification_service,
        buyer_id: int,
        supply_request: Dict[str, Any],
        match: Dict[str, Any],
        confirmed: bool,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Notify buyer when farmer confirms or rejects a match

        Args:
            notification_service: NotificationService instance
            buyer_id: ID of the buyer
            supply_request: Supply request data
            match: Match data
            confirmed: Whether farmer confirmed or rejected
            notes: Optional notes from farmer

        Returns:
            Notification result dictionary
        """
        from app.orm.user import User

        # Get buyer details
        user_model = User()
        buyer = user_model.find(buyer_id)

        if not buyer:
            logger.warning(f"Buyer {buyer_id} not found for notification")
            return {"success": False, "error": "Buyer not found"}

        buyer_name = buyer.get("name", "Buyer")
        buyer_phone = buyer.get("phone")
        buyer_email = buyer.get("email")

        crop_type = supply_request.get("crop_type")
        quantity = match.get("matched_quantity")

        if confirmed:
            subject = f"✅ Farmer Confirmed - {crop_type} Supply Match"
            message = f"""Hello {buyer_name},

Good news! The farmer has confirmed your supply match.

Match Details:
- Crop: {crop_type}
- Quantity: {quantity:.2f} kg
- Farmer ID: {match.get('farmer_id')}
- Match Score: {match.get('match_score'):.0f}%

Status: CONFIRMED ✅

Next Steps:
1. Complete advance payment (30%) within 3 days
2. Schedule quality verification
3. Coordinate delivery logistics
4. Track order progress

{f"Farmer's Notes: {notes}" if notes else ""}

Login to CropSense AI to proceed with payment and view complete order details."""
        else:
            subject = f"❌ Farmer Declined - {crop_type} Supply Match"
            message = f"""Hello {buyer_name},

Unfortunately, the farmer has declined your supply match.

Match Details:
- Crop: {crop_type}
- Quantity: {quantity:.2f} kg
- Farmer ID: {match.get('farmer_id')}

Status: DECLINED ❌

{f"Farmer's Reason: {notes}" if notes else ""}

Don't worry! We're finding alternative matches for you.

Next Steps:
1. Review other available matches
2. We'll notify you of new matches
3. Consider adjusting requirements if needed

Login to CropSense AI to view alternative supply options."""

        # Send notification
        try:
            result = notification_service._send_notification(
                topic_arn=notification_service.topic_booking_notifications,
                subject=subject,
                message=message,
                phone_number=buyer_phone,
                email=buyer_email,
                notification_type="farmer_confirmation_update",
                metadata={
                    "buyer_id": buyer_id,
                    "match_id": match.get("id"),
                    "crop_type": crop_type,
                    "confirmed": confirmed,
                },
            )

            logger.info(f"Farmer confirmation notification sent to buyer {buyer_id}")
            return result

        except Exception as e:
            logger.error(
                f"Failed to send farmer confirmation notification to buyer {buyer_id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "notification_type": "farmer_confirmation_update",
            }

    def _check_aggregated_group_status(self, aggregation_group_id: str) -> None:
        """
        Check if all farmers in an aggregated group have confirmed
        Update supply request status accordingly

        Args:
            aggregation_group_id: ID of the aggregation group
        """
        match_model = SupplyMatch()
        request_model = SupplyRequest()

        # Get all matches in the group
        matches = match_model.where("aggregation_group_id", aggregation_group_id).get()

        if not matches:
            return

        # Count confirmations
        total = len(matches)
        confirmed = len([m for m in matches if m.get("farmer_confirmation_status") == "confirmed"])
        rejected = len([m for m in matches if m.get("farmer_confirmation_status") == "rejected"])
        pending = total - confirmed - rejected

        logger.info(
            f"Aggregated group {aggregation_group_id}: {confirmed}/{total} confirmed, {rejected} rejected, {pending} pending"
        )

        # If all confirmed, update supply request to in_progress
        if confirmed == total:
            request_id = matches[0].get("request_id")
            request_model.update(
                request_id, {"status": "in_progress", "updated_at": datetime.now()}
            )
            logger.info(
                f"All farmers confirmed for aggregated group {aggregation_group_id}, supply request {request_id} now in_progress"
            )

    def _handle_aggregated_rejection(self, rejected_match: Dict[str, Any]) -> None:
        """
        Handle farmer rejection in an aggregated group
        Try to find replacement farmer

        Args:
            rejected_match: The rejected match data
        """
        logger.info(
            f"Handling rejection in aggregated group {rejected_match.get('aggregation_group_id')}"
        )

        # Get supply request
        request_model = SupplyRequest()
        supply_request = request_model.find(rejected_match.get("request_id"))

        if not supply_request:
            return

        # Find replacement matches for the rejected quantity
        rejected_quantity = rejected_match.get("matched_quantity")

        # This would trigger a new matching search for the remaining quantity
        # For now, just log it - full implementation would call find_matches again
        logger.warning(
            f"Need to find replacement for {rejected_quantity}kg in aggregated group {rejected_match.get('aggregation_group_id')}"
        )

    def get_coordination_status(self, request_id: int) -> Dict[str, Any]:
        """
        Get coordination status for a supply request
        Shows farmer confirmations, delivery status, payment status

        Args:
            request_id: ID of the supply request

        Returns:
            Dict with coordination details
        """
        from app.orm.advance_booking import AdvanceBooking
        from app.orm.payment_milestone import PaymentMilestone

        match_model = SupplyMatch()
        booking_model = AdvanceBooking()
        milestone_model = PaymentMilestone()
        request_model = SupplyRequest()

        # Get supply request
        supply_request = request_model.find(request_id)
        if not supply_request:
            raise ValueError(f"Supply request {request_id} not found")

        # Get all matches
        matches = (
            match_model.where("request_id", request_id).where("status", "buyer_accepted").get()
        )

        if not matches:
            return {
                "request_id": request_id,
                "status": supply_request.get("status"),
                "message": "No accepted matches found",
            }

        # Group by aggregation
        single_matches = [m for m in matches if not m.get("is_aggregated")]
        aggregated_groups = {}

        for match in matches:
            if match.get("is_aggregated"):
                group_id = match.get("aggregation_group_id")
                if group_id not in aggregated_groups:
                    aggregated_groups[group_id] = []
                aggregated_groups[group_id].append(match)

        # Build coordination status
        coordination_data = {
            "request_id": request_id,
            "request_status": supply_request.get("status"),
            "crop_type": supply_request.get("crop_type"),
            "total_quantity_needed": supply_request.get("quantity_needed"),
            "single_farmer_matches": [],
            "aggregated_groups": [],
        }

        # Process single matches
        for match in single_matches:
            booking = (
                booking_model.where("listing_id", match.get("listing_id"))
                .where("farmer_id", match.get("farmer_id"))
                .first()
            )

            payment_status = "pending"
            if booking:
                milestones = milestone_model.where("booking_id", booking.get("id")).get()
                paid = len([m for m in milestones if m.get("status") == "paid"])
                total = len(milestones)
                payment_status = f"{paid}/{total} milestones paid"

            coordination_data["single_farmer_matches"].append(
                {
                    "match_id": match.get("id"),
                    "farmer_id": match.get("farmer_id"),
                    "quantity": match.get("matched_quantity"),
                    "farmer_confirmation": match.get("farmer_confirmation_status"),
                    "delivery_status": match.get("delivery_status"),
                    "payment_status": payment_status,
                    "booking_id": booking.get("id") if booking else None,
                }
            )

        # Process aggregated groups
        for group_id, group_matches in aggregated_groups.items():
            total_quantity = sum(m.get("matched_quantity", 0) for m in group_matches)
            confirmed_count = len(
                [m for m in group_matches if m.get("farmer_confirmation_status") == "confirmed"]
            )

            farmers = []
            for match in group_matches:
                booking = (
                    booking_model.where("listing_id", match.get("listing_id"))
                    .where("farmer_id", match.get("farmer_id"))
                    .first()
                )

                payment_status = "pending"
                if booking:
                    milestones = milestone_model.where("booking_id", booking.get("id")).get()
                    paid = len([m for m in milestones if m.get("status") == "paid"])
                    total = len(milestones)
                    payment_status = f"{paid}/{total} paid"

                farmers.append(
                    {
                        "match_id": match.get("id"),
                        "farmer_id": match.get("farmer_id"),
                        "quantity": match.get("matched_quantity"),
                        "farmer_confirmation": match.get("farmer_confirmation_status"),
                        "delivery_status": match.get("delivery_status"),
                        "payment_status": payment_status,
                        "booking_id": booking.get("id") if booking else None,
                    }
                )

            coordination_data["aggregated_groups"].append(
                {
                    "group_id": group_id,
                    "total_farmers": len(group_matches),
                    "confirmed_farmers": confirmed_count,
                    "total_quantity": total_quantity,
                    "farmers": farmers,
                    "coordination_status": (
                        "all_confirmed"
                        if confirmed_count == len(group_matches)
                        else "pending_confirmations"
                    ),
                }
            )

        return coordination_data

    def update_delivery_status(
        self, match_id: int, delivery_status: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update delivery status for a match

        Args:
            match_id: ID of the match
            delivery_status: New delivery status (pending, in_transit, delivered, failed)
            notes: Optional delivery notes

        Returns:
            Dict with update status
        """
        match_model = SupplyMatch()

        # Get the match
        match = match_model.find(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        # Update delivery status
        update_data = {"delivery_status": delivery_status, "updated_at": datetime.now()}

        if notes:
            existing_notes = match.get("delivery_notes", "")
            update_data["delivery_notes"] = (
                f"{existing_notes}\n[{datetime.now().isoformat()}] {notes}"
                if existing_notes
                else notes
            )

        match_model.update(match_id, update_data)

        logger.info(f"Updated delivery status for match {match_id} to {delivery_status}")

        return {
            "success": True,
            "match_id": match_id,
            "delivery_status": delivery_status,
            "message": f"Delivery status updated to {delivery_status}",
        }
