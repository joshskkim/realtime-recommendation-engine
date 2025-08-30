"""
Redis cache service for recommendations
"""

import redis
import json
import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_client = None
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        
        # TTL settings from environment
        self.ttl_user_profile = int(os.getenv("CACHE_TTL_USER_PROFILE", "3600"))
        self.ttl_recommendations = int(os.getenv("CACHE_TTL_RECOMMENDATIONS", "1800"))
        self.ttl_item_features = int(os.getenv("CACHE_TTL_ITEM_FEATURES", "7200"))
        self.ttl_popularity = int(os.getenv("CACHE_TTL_POPULARITY", "600"))
    
    async def start(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self._ping()
            logger.info("✅ Redis cache service started")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    async def _ping(self):
        """Test Redis connection"""
        if self.redis_client:
            return self.redis_client.ping()
        return False
    
    def _key_recommendations(self, user_id: int, algorithm: str = "default") -> str:
        """Generate cache key for user recommendations"""
        return f"rec:user:{user_id}:{algorithm}"
    
    def _key_user_profile(self, user_id: int) -> str:
        """Generate cache key for user profile"""
        return f"profile:user:{user_id}"
    
    def _key_item_features(self, item_id: int) -> str:
        """Generate cache key for item features"""
        return f"features:item:{item_id}"
    
    def _key_popularity(self, category: str = "all") -> str:
        """Generate cache key for popularity scores"""
        return f"popularity:{category}"
    
    def _key_similar_items(self, item_id: int) -> str:
        """Generate cache key for similar items"""
        return f"similar:item:{item_id}"
    
    async def get_recommendations(self, user_id: int, algorithm: str = "default") -> Optional[List[Dict]]:
        """Get cached recommendations for user"""
        if not self.redis_client:
            return None
        
        try:
            key = self._key_recommendations(user_id, algorithm)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error getting cached recommendations: {e}")
        return None
    
    async def cache_recommendations(self, user_id: int, recommendations: List[Dict], 
                                  algorithm: str = "default"):
        """Cache user recommendations"""
        if not self.redis_client:
            return
        
        try:
            key = self._key_recommendations(user_id, algorithm)
            self.redis_client.setex(
                key,
                self.ttl_recommendations,
                json.dumps(recommendations)
            )
            logger.debug(f"Cached {len(recommendations)} recommendations for user {user_id}")
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get cached user profile"""
        if not self.redis_client:
            return None
        
        try:
            key = self._key_user_profile(user_id)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error getting cached user profile: {e}")
        return None
    
    async def cache_user_profile(self, user_id: int, profile: Dict):
        """Cache user profile"""
        if not self.redis_client:
            return
        
        try:
            key = self._key_user_profile(user_id)
            self.redis_client.setex(
                key,
                self.ttl_user_profile,
                json.dumps(profile)
            )
        except Exception as e:
            logger.error(f"Error caching user profile: {e}")
    
    async def get_item_features(self, item_id: int) -> Optional[Dict]:
        """Get cached item features"""
        if not self.redis_client:
            return None
        
        try:
            key = self._key_item_features(item_id)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error getting cached item features: {e}")
        return None
    
    async def cache_item_features(self, item_id: int, features: Dict):
        """Cache item features"""
        if not self.redis_client:
            return
        
        try:
            key = self._key_item_features(item_id)
            self.redis_client.setex(
                key,
                self.ttl_item_features,
                json.dumps(features)
            )
        except Exception as e:
            logger.error(f"Error caching item features: {e}")
    
    async def get_popular_items(self, category: str = "all", limit: int = 100) -> Optional[List[Dict]]:
        """Get cached popular items"""
        if not self.redis_client:
            return None
        
        try:
            key = self._key_popularity(category)
            cached = self.redis_client.get(key)
            if cached:
                items = json.loads(cached)
                return items[:limit]
        except Exception as e:
            logger.error(f"Error getting cached popular items: {e}")
        return None
    
    async def cache_popular_items(self, items: List[Dict], category: str = "all"):
        """Cache popular items"""
        if not self.redis_client:
            return
        
        try:
            key = self._key_popularity(category)
            self.redis_client.setex(
                key,
                self.ttl_popularity,
                json.dumps(items)
            )
        except Exception as e:
            logger.error(f"Error caching popular items: {e}")
    
    async def get_similar_items(self, item_id: int) -> Optional[List[Dict]]:
        """Get cached similar items"""
        if not self.redis_client:
            return None
        
        try:
            key = self._key_similar_items(item_id)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error getting cached similar items: {e}")
        return None
    
    async def cache_similar_items(self, item_id: int, similar_items: List[Dict]):
        """Cache similar items"""
        if not self.redis_client:
            return
        
        try:
            key = self._key_similar_items(item_id)
            self.redis_client.setex(
                key,
                self.ttl_item_features,
                json.dumps(similar_items)
            )
        except Exception as e:
            logger.error(f"Error caching similar items: {e}")
    
    async def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user"""
        if not self.redis_client:
            return
        
        try:
            # Get all keys for this user
            patterns = [
                f"rec:user:{user_id}:*",
                f"profile:user:{user_id}"
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logger.debug(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, 
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}