"""
Basic FastAPI ML Service for Recommendation Engine
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import redis
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Recommendation ML Service",
    description="Real-time recommendation engine ML service",
    version="0.1.0",
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


# Basic models
class HealthResponse(BaseModel):
    status: str
    service: str
    redis_connected: bool


class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = 10


class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[Dict[str, Any]]
    algorithm: str


# Routes
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
        redis_connected=redis_connected
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Recommendation ML Service", "version": "0.1.0"}


@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Get recommendations for a user"""
    # Basic mock recommendations for now
    mock_recommendations = [
        {"item_id": i, "score": 0.9 - (i * 0.1), "reason": "popular"}
        for i in range(1, min(request.limit + 1, 11))
    ]
    
    return RecommendationResponse(
        user_id=request.user_id,
        recommendations=mock_recommendations,
        algorithm="mock"
    )


@app.get("/recommendations/user/{user_id}")
async def get_user_recommendations(user_id: int, limit: int = 10):
    """Get recommendations for a specific user"""
    request = RecommendationRequest(user_id=user_id, limit=limit)
    return await get_recommendations(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)