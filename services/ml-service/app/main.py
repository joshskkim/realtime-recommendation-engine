"""
Real-time Recommendation Engine - ML Service (Simplified)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import redis
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Recommendation ML Service",
    description="Real-time recommendation engine with hybrid algorithms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection (with error handling)
try:
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379"),
        decode_responses=True
    )
    redis_client.ping()
    logger.info("✅ Connected to Redis")
except Exception as e:
    logger.warning(f"⚠️  Redis connection failed: {e}")
    redis_client = None

# Mock data for testing
MOCK_USERS = list(range(1, 101))
MOCK_ITEMS = list(range(1, 501))
MOCK_CATEGORIES = ["movies", "books", "music", "technology", "sports"]

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    redis_connected: bool
    ml_model_trained: bool = True
    
    model_config = {"protected_namespaces": ()}

class InteractionRequest(BaseModel):
    user_id: int
    item_id: int
    interaction_type: str
    rating: Optional[float] = None
    session_id: Optional[str] = None

class RecommendationItem(BaseModel):
    item_id: int
    title: str
    category: str
    score: float
    algorithm: str
    explanation: str

class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[RecommendationItem]
    algorithm: str
    timestamp: str
    cached: bool = False

class SimilarItemsResponse(BaseModel):
    item_id: int
    similar_items: List[RecommendationItem]
    timestamp: str

# Helper functions
def generate_mock_recommendations(user_id: int, limit: int = 10, algorithm: str = "hybrid") -> List[RecommendationItem]:
    """Generate mock recommendations"""
    import random
    random.seed(user_id)  # Consistent results for same user
    
    recommendations = []
    for i in range(limit):
        item_id = random.choice(MOCK_ITEMS)
        category = random.choice(MOCK_CATEGORIES)
        score = round(random.uniform(0.5, 1.0), 3)
        
        recommendations.append(RecommendationItem(
            item_id=item_id,
            title=f"{category.title()} Item {item_id}",
            category=category,
            score=score,
            algorithm=algorithm,
            explanation=f"Recommended based on {algorithm} algorithm"
        ))
    
    return recommendations

def get_cached_recommendations(user_id: int, algorithm: str) -> Optional[List[RecommendationItem]]:
    """Get cached recommendations"""
    if not redis_client:
        return None
    
    try:
        key = f"rec:user:{user_id}:{algorithm}"
        cached = redis_client.get(key)
        if cached:
            data = json.loads(cached)
            return [RecommendationItem(**item) for item in data]
    except Exception as e:
        logger.error(f"Cache error: {e}")
    return None

def cache_recommendations(user_id: int, recommendations: List[RecommendationItem], algorithm: str):
    """Cache recommendations"""
    if not redis_client:
        return
    
    try:
        key = f"rec:user:{user_id}:{algorithm}"
        data = [rec.dict() for rec in recommendations]
        redis_client.setex(key, 1800, json.dumps(data))  # 30 min TTL
    except Exception as e:
        logger.error(f"Cache error: {e}")

# API Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    redis_connected = False
    if redis_client:
        try:
            redis_client.ping()
            redis_connected = True
        except:
            pass
    
    return HealthResponse(
        status="healthy",
        service="ml-service",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        redis_connected=redis_connected,
        ml_model_trained=True
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Real-time Recommendation Engine - ML Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "recommendations": "/recommendations/user/{user_id}",
            "similar_items": "/items/{item_id}/similar",
            "record_interaction": "/interactions"
        }
    }

@app.get("/recommendations/user/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: int, 
    limit: int = 10, 
    algorithm: str = "hybrid"
):
    """Get recommendations for a specific user"""
    try:
        # Check cache first
        cached_recs = get_cached_recommendations(user_id, algorithm)
        if cached_recs:
            logger.info(f"Returning cached recommendations for user {user_id}")
            return RecommendationResponse(
                user_id=user_id,
                recommendations=cached_recs[:limit],
                algorithm=algorithm,
                timestamp=datetime.now().isoformat(),
                cached=True
            )
        
        # Generate new recommendations
        recommendations = generate_mock_recommendations(user_id, limit, algorithm)
        
        # Cache them
        cache_recommendations(user_id, recommendations, algorithm)
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        
        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            algorithm=algorithm,
            timestamp=datetime.now().isoformat(),
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.get("/items/{item_id}/similar", response_model=SimilarItemsResponse)
async def get_similar_items(item_id: int, limit: int = 10):
    """Get items similar to the specified item"""
    try:
        # Generate similar items (mock)
        similar_items = generate_mock_recommendations(item_id, limit, "similarity")
        
        return SimilarItemsResponse(
            item_id=item_id,
            similar_items=similar_items,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting similar items for item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get similar items: {str(e)}")

@app.post("/interactions")
async def record_interaction(interaction: InteractionRequest, background_tasks: BackgroundTasks):
    """Record a user interaction"""
    try:
        # Log the interaction
        logger.info(f"Recording interaction: user {interaction.user_id} -> item {interaction.item_id} ({interaction.interaction_type})")
        
        # Invalidate user's cache
        if redis_client:
            try:
                pattern = f"rec:user:{interaction.user_id}:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
                    logger.debug(f"Invalidated cache for user {interaction.user_id}")
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")
        
        return {
            "message": "Interaction recorded successfully",
            "user_id": interaction.user_id,
            "item_id": interaction.item_id,
            "interaction_type": interaction.interaction_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    if not redis_client:
        return {"error": "Redis not connected"}
    
    try:
        info = redis_client.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "0B"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_keys": len(redis_client.keys("*"))
        }
    except Exception as e:
        return {"error": str(e)}

@app.delete("/cache/user/{user_id}")
async def invalidate_user_cache(user_id: int):
    """Invalidate cache for a specific user"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Cache service not available")
    
    try:
        pattern = f"rec:user:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        
        return {
            "message": f"Cache invalidated for user {user_id}",
            "keys_deleted": len(keys),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)