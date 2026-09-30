"""
API Response Caching Utility
Provides Redis-based caching for API responses and database query results

Task 18.1: Redis caching for frequently accessed data
- Bedrock API responses: 6-hour TTL
- Market intelligence data: 24-hour TTL
- Farm profiles and crop recommendations: 1-hour TTL
- Cache invalidation strategies for data updates
"""

import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# TTL Constants (in seconds) - Task 18.1 Requirements
TTL_BEDROCK_API = 6 * 60 * 60  # 6 hours for Bedrock API responses
TTL_MARKET_DATA = 24 * 60 * 60  # 24 hours for market intelligence data
TTL_FARM_PROFILE = 1 * 60 * 60  # 1 hour for farm profiles
TTL_CROP_RECOMMENDATIONS = 1 * 60 * 60  # 1 hour for crop recommendations
TTL_SHORT = 5 * 60  # 5 minutes for frequently changing data
TTL_DEFAULT = 5 * 60  # 5 minutes default


class CacheManager:
    """
    Redis-based cache manager for API responses and database queries

    Features:
    - TTL-based expiration
    - Key namespacing
    - JSON serialization
    - Error handling with fallback
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,  # 5 minutes
        enabled: bool = True,
    ):
        """
        Initialize cache manager

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            enabled: Enable/disable caching
        """
        self.enabled = enabled
        self.default_ttl = default_ttl

        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except RedisError as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("Caching disabled")

    def close(self):
        """Close Redis connection and cleanup resources"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.close()
        return False

    def _generate_cache_key(self, namespace: str, *args, **kwargs) -> str:
        """
        Generate cache key from namespace and arguments

        Args:
            namespace: Cache key namespace
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)

        # Hash long keys
        if len(key_string) > 100:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{namespace}:{key_hash}"

        return f"{namespace}:{key_string}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (falls back to Firestore if Redis is disabled)

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            try:
                from datetime import datetime

                from app.services.firestore_service import firestore_service

                cached = firestore_service.get_document("cache", key.replace(":", "_"))
                if cached:
                    expires_at_str = cached.get("expires_at")
                    if expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if expires_at < datetime.utcnow():
                            # Expired
                            firestore_service.get_collection("cache").document(
                                key.replace(":", "_")
                            ).delete()
                            return None
                    return cached.get("value")
                return None
            except Exception as e:
                logger.warning(f"Firestore fallback cache get error for key {key}: {e}")
                return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache (falls back to Firestore if Redis is disabled)

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            try:
                from datetime import datetime

                from app.services.firestore_service import firestore_service

                ttl = ttl or self.default_ttl
                expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
                data = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow().isoformat(),
                }
                firestore_service.set_document("cache", key.replace(":", "_"), data)
                return True
            except Exception as e:
                logger.warning(f"Firestore fallback cache set error for key {key}: {e}")
                return False

        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache (falls back to Firestore if Redis is disabled)

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            try:
                from app.services.firestore_service import firestore_service

                firestore_service.get_collection("cache").document(key.replace(":", "_")).delete()
                return True
            except Exception as e:
                logger.warning(f"Firestore fallback cache delete error for key {key}: {e}")
                return False

        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "farms:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def clear(self) -> bool:
        """
        Clear all cache entries

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            return True
        except RedisError as e:
            logger.warning(f"Cache clear error: {e}")
            return False

    def invalidate_farm_cache(self, farm_id: int) -> int:
        """
        Invalidate all cache entries related to a specific farm

        Args:
            farm_id: Farm ID

        Returns:
            Number of keys deleted
        """
        patterns = [
            f"farm:{farm_id}:*",
            f"farm_profile:{farm_id}",
            f"crop_recommendations:*:farm_id={farm_id}*",
            f"annual_strategy:*:farm_id={farm_id}*",
        ]

        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)

        logger.info(f"Invalidated {total_deleted} cache entries for farm {farm_id}")
        return total_deleted

    def invalidate_market_data_cache(
        self, crop_type: Optional[str] = None, state: Optional[str] = None
    ) -> int:
        """
        Invalidate market intelligence data cache

        Args:
            crop_type: Specific crop type (optional)
            state: Specific state (optional)

        Returns:
            Number of keys deleted
        """
        if crop_type and state:
            pattern = f"market_data:*crop_type={crop_type}*state={state}*"
        elif crop_type:
            pattern = f"market_data:*crop_type={crop_type}*"
        elif state:
            pattern = f"market_data:*state={state}*"
        else:
            pattern = "market_data:*"

        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} market data cache entries")
        return deleted

    def invalidate_crop_recommendations_cache(
        self, state: Optional[str] = None, season: Optional[str] = None
    ) -> int:
        """
        Invalidate crop recommendations cache

        Args:
            state: Specific state (optional)
            season: Specific season (optional)

        Returns:
            Number of keys deleted
        """
        if state and season:
            pattern = f"crop_recommendations:*state={state}*season={season}*"
        elif state:
            pattern = f"crop_recommendations:*state={state}*"
        elif season:
            pattern = f"crop_recommendations:*season={season}*"
        else:
            pattern = "crop_recommendations:*"

        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} crop recommendations cache entries")
        return deleted

    def invalidate_bedrock_cache(self, cache_key_pattern: Optional[str] = None) -> int:
        """
        Invalidate Bedrock API response cache

        Args:
            cache_key_pattern: Specific pattern to match (optional)

        Returns:
            Number of keys deleted
        """
        pattern = cache_key_pattern or "bedrock:*"
        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} Bedrock cache entries")
        return deleted


def cached(namespace: str, ttl: Optional[int] = None, cache_manager: Optional[CacheManager] = None):
    """
    Decorator for caching function results

    Args:
        namespace: Cache key namespace
        ttl: TTL in seconds (uses cache manager default if None)
        cache_manager: CacheManager instance (uses global if None)

    Example:
        @cached("farms", ttl=3600)
        def get_farm(farm_id: int):
            rows = DB.raw("SELECT * FROM farms WHERE id = ?", [farm_id]).result  # app.core.db.DB
            return rows[0] if rows else None
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use global cache manager if not provided
            cm = cache_manager or get_cache_manager()

            if not cm or not cm.enabled:
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = cm._generate_cache_key(namespace, *args, **kwargs)

            # Try to get from cache
            cached_value = cm.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)

            # Cache result
            if result is not None:
                cm.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def init_cache_manager(
    redis_url: str = "redis://localhost:6379/0", default_ttl: int = 300, enabled: bool = True
) -> CacheManager:
    """
    Initialize global cache manager

    Args:
        redis_url: Redis connection URL
        default_ttl: Default TTL in seconds
        enabled: Enable/disable caching

    Returns:
        CacheManager instance
    """
    global _cache_manager
    _cache_manager = CacheManager(redis_url=redis_url, default_ttl=default_ttl, enabled=enabled)
    return _cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """
    Get global cache manager instance

    Returns:
        CacheManager instance or None
    """
    return _cache_manager
