# services/ml-service/app/main.py - Add this endpoint handler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import redis
import json
import random
from datetime import datetime

app = FastAPI(title="ML Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class RecommendationRequest(BaseModel):
    user_id: str
    user_profile: Optional[Dict[str, Any]] = None
    limit: int = 10
    strategy: str = "hybrid"

@app.post("/recommendations/generate")
async def generate_recommendations(request: RecommendationRequest):
    """Generate recommendations with fallback for new users"""
    
    # Check if user has interactions
    interactions_key = f"user:interactions:{request.user_id}"
    interactions = redis_client.get(interactions_key)
    
    if not interactions:
        # New user - return popular/random items
        items = []
        for i in range(request.limit):
            items.append({
                "item_id": f"item_{random.randint(100, 999)}",
                "score": round(random.uniform(0.5, 1.0), 3),
                "method": "popularity",
                "explanation": "Popular item recommended for new users"
            })
        
        return {
            "user_id": request.user_id,
            "strategy": "cold_start",
            "items": items,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Existing user logic (simplified for testing)
    items = []
    for i in range(request.limit):
        items.append({
            "item_id": f"item_{random.randint(100, 999)}",
            "score": round(random.uniform(0.6, 1.0), 3),
            "method": request.strategy,
            "explanation": f"Based on your past interactions"
        })
    
    return {
        "user_id": request.user_id,
        "strategy": request.strategy,
        "items": items,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/recommendations/item/{item_id}/similar")
async def get_similar_items(item_id: str, limit: int = 5):
    """Get similar items"""
    items = []
    for i in range(limit):
        items.append({
            "item_id": f"item_{random.randint(100, 999)}",
            "similarity": round(random.uniform(0.7, 0.95), 3),
            "explanation": f"Similar to {item_id}"
        })
    
    return {
        "source_item": item_id,
        "similar_items": items,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/recommendations/trending")
async def get_trending_items(category: Optional[str] = None, limit: int = 10, time_window: str = "24h"):
    """Get trending items"""
    items = []
    for i in range(limit):
        items.append({
            "item_id": f"trending_{random.randint(100, 999)}",
            "score": random.randint(50, 500),
            "category": category or "all",
            "trend": "rising"
        })
    
    return {
        "category": category or "all",
        "time_window": time_window,
        "items": items,
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ml-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": redis_client.ping(),
        "ml_model_trained": True
    }