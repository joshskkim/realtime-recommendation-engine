"""
Recommendation API endpoints
File: services/ml-service/app/api/recommendations.py
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
import redis
import json
import numpy as np
from app.core import config

router = APIRouter()

# Initialize Redis connection
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True
)

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[Dict]
    strategy: str
    cached: bool = False

class SimilarItemsRequest(BaseModel):
    item_id: str
    limit: int = 5

@router.get("/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(default=10, le=50)
) -> RecommendationResponse:
    """Get personalized recommendations for a user"""
    
    # Check cache first
    cache_key = f"recommendations:{user_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        recommendations = json.loads(cached_data)
        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations[:limit],
            strategy="cached",
            cached=True
        )
    
    # Generate recommendations using collaborative filtering
    recommendations = await generate_cf_recommendations(user_id, limit)
    
    # Cache the results
    redis_client.setex(
        cache_key,
        config.CACHE_TTL_SECONDS,
        json.dumps(recommendations)
    )
    
    return RecommendationResponse(
        user_id=user_id,
        recommendations=recommendations,
        strategy="collaborative_filtering",
        cached=False
    )

@router.get("/item/{item_id}/similar")
async def get_similar_items(
    item_id: str,
    limit: int = Query(default=5, le=20)
) -> Dict:
    """Get items similar to a given item"""
    
    # Generate similar items using content-based filtering
    similar_items = await generate_similar_items(item_id, limit)
    
    return {
        "item_id": item_id,
        "similar_items": similar_items,
        "count": len(similar_items)
    }

@router.post("/batch")
async def get_batch_recommendations(user_ids: List[str]) -> Dict:
    """Get recommendations for multiple users"""
    
    if len(user_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 users per batch request"
        )
    
    results = {}
    for user_id in user_ids:
        # Check cache
        cache_key = f"recommendations:{user_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            results[user_id] = json.loads(cached_data)[:10]
        else:
            results[user_id] = await generate_cf_recommendations(user_id, 10)
    
    return {
        "users": len(user_ids),
        "recommendations": results
    }

@router.get("/popular")
async def get_popular_items(
    limit: int = Query(default=10, le=50),
    time_window: str = Query(default="24h", regex="^(1h|6h|24h|7d|30d)$")
) -> Dict:
    """Get globally popular items"""
    
    # Get from cache
    cache_key = f"popular_items:{time_window}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        items = json.loads(cached_data)
        return {
            "items": items[:limit],
            "time_window": time_window,
            "cached": True
        }
    
    # Generate popular items
    popular_items = await generate_popular_items(limit, time_window)
    
    # Cache for shorter duration
    redis_client.setex(cache_key, 300, json.dumps(popular_items))
    
    return {
        "items": popular_items,
        "time_window": time_window,
        "cached": False
    }

async def generate_cf_recommendations(user_id: str, limit: int) -> List[Dict]:
    """Generate collaborative filtering recommendations"""
    
    # Mock implementation - replace with actual CF algorithm
    recommendations = []
    for i in range(limit):
        recommendations.append({
            "item_id": f"item_{np.random.randint(1000, 9999)}",
            "score": round(0.9 - (i * 0.05), 3),
            "reason": "users_also_liked"
        })
    
    return recommendations

async def generate_similar_items(item_id: str, limit: int) -> List[Dict]:
    """Generate similar items using content-based filtering"""
    
    # Mock implementation - replace with actual similarity calculation
    similar = []
    for i in range(limit):
        similar.append({
            "item_id": f"similar_{np.random.randint(100, 999)}",
            "similarity_score": round(0.95 - (i * 0.1), 3),
            "matched_features": ["category", "price_range"]
        })
    
    return similar

async def generate_popular_items(limit: int, time_window: str) -> List[Dict]:
    """Generate popular items for time window"""
    
    # Mock implementation
    items = []
    for i in range(limit):
        items.append({
            "item_id": f"popular_{np.random.randint(100, 999)}",
            "popularity_score": round(100 - (i * 5), 1),
            "interaction_count": 1000 - (i * 50)
        })
    
    return items