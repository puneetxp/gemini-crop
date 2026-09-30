"""
Vector Search Service using pgvector for crop similarity matching
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.crop import CropRecommendation
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for vector similarity search using pgvector"""

    def __init__(self):
        # Initialize Bedrock service for embeddings (Cloud-based replaced local ML)
        self.bedrock_service = BedrockService()
        # Stick to 384 dimensions for compatibility with existing DB schema
        self.embedding_dimension = 384

    def generate_embedding(self, features: Dict[str, Any]) -> List[float]:
        """Generate embedding vector from farm/crop features using Cloud Bedrock"""
        try:
            # Convert features to text representation
            feature_text = self._features_to_text(features)

            # Generate embedding using Bedrock (removes load of local ML models)
            embedding = self.bedrock_service.generate_embedding(feature_text)

            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding via Bedrock: {e}")
            raise

    def _features_to_text(self, features: Dict[str, Any]) -> str:
        """Convert feature dictionary to text for embedding generation"""
        text_parts = []

        # Soil features
        if "soil_type" in features:
            text_parts.append(f"soil_type:{features['soil_type']}")
        if "ph_level" in features:
            text_parts.append(f"ph:{features['ph_level']}")
        if "nitrogen" in features:
            text_parts.append(f"nitrogen:{features['nitrogen']}")

        # Climate features
        if "temperature_avg" in features:
            text_parts.append(f"temperature:{features['temperature_avg']}")
        if "rainfall_avg" in features:
            text_parts.append(f"rainfall:{features['rainfall_avg']}")

        # Farm features
        if "irrigation_type" in features:
            text_parts.append(f"irrigation:{features['irrigation_type']}")
        if "area" in features:
            text_parts.append(f"area:{features['area']}")

        return " ".join(text_parts)

    def find_similar_crops(
        self,
        db: Session,
        query_features: Dict[str, Any],
        similarity_threshold: float = 0.7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find similar crops using pgvector similarity search"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_features)

            # Execute vector similarity search
            query = text("""
            SELECT 
                cv.id,
                cv.crop_type,
                cv.variety_name,
                cv.growth_duration,
                cv.water_requirement,
                cv.market_demand_score,
                1 - (cv.embedding <=> :query_vector) as similarity_score
            FROM crop_varieties cv
            WHERE 1 - (cv.embedding <=> :query_vector) > :threshold
            ORDER BY cv.embedding <=> :query_vector
            LIMIT :limit
            """)

            result = db.execute(
                query,
                {
                    "query_vector": query_embedding,
                    "threshold": similarity_threshold,
                    "limit": limit,
                },
            )

            # Convert results to list of dictionaries
            similar_crops = []
            for row in result:
                similar_crops.append(
                    {
                        "id": str(row.id),
                        "crop_type": row.crop_type,
                        "variety_name": row.variety_name,
                        "growth_duration": row.growth_duration,
                        "water_requirement": row.water_requirement,
                        "market_demand_score": (
                            float(row.market_demand_score) if row.market_demand_score else 0.0
                        ),
                        "similarity_score": float(row.similarity_score),
                    }
                )

            logger.info(f"Found {len(similar_crops)} similar crops")
            return similar_crops

        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            raise

    def update_crop_embedding(self, db: Session, crop_variety_id: str, features: Dict[str, Any]):
        """Update embedding for a crop variety"""
        try:
            # Generate new embedding
            embedding = self.generate_embedding(features)

            # Update in database
            update_query = text("""
            UPDATE crop_varieties 
            SET embedding = :embedding, updated_at = CURRENT_TIMESTAMP
            WHERE id = :crop_id
            """)

            db.execute(update_query, {"embedding": embedding, "crop_id": crop_variety_id})

            db.commit()
            logger.info(f"Updated embedding for crop variety {crop_variety_id}")

        except Exception as e:
            logger.error(f"Error updating crop embedding: {e}")
            db.rollback()
            raise

    def batch_update_embeddings(self, db: Session, crop_features_list: List[Dict[str, Any]]):
        """Batch update embeddings for multiple crop varieties"""
        try:
            for crop_features in crop_features_list:
                crop_id = crop_features.pop("id")
                self.update_crop_embedding(db, crop_id, crop_features)

            logger.info(f"Batch updated {len(crop_features_list)} crop embeddings")

        except Exception as e:
            logger.error(f"Error in batch embedding update: {e}")
            raise

    def search_by_text(self, db: Session, search_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search crops by text description using vector similarity"""
        try:
            # Generate embedding from search text using Bedrock
            embedding = self.bedrock_service.generate_embedding(search_text)

            # Execute search
            query = text("""
            SELECT 
                cv.id,
                cv.crop_type,
                cv.variety_name,
                1 - (cv.embedding <=> :query_vector) as similarity_score
            FROM crop_varieties cv
            ORDER BY cv.embedding <=> :query_vector
            LIMIT :limit
            """)

            result = db.execute(query, {"query_vector": embedding, "limit": limit})

            search_results = []
            for row in result:
                search_results.append(
                    {
                        "id": str(row.id),
                        "crop_type": row.crop_type,
                        "variety_name": row.variety_name,
                        "similarity_score": float(row.similarity_score),
                    }
                )

            return search_results

        except Exception as e:
            logger.error(f"Error in text-based vector search: {e}")
            raise
