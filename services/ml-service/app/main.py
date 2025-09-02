"""
Updated main.py for ML Service with Phase 3 features
File: services/ml-service/app/main.py
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

# Import Phase 3 components
from app.core.cold_start import ColdStartHandler, UserDemographics
from app.core.ab_testing import ABTestingFramework
from app.core.recommendation_strategies import StrategyManager
from app.api.ab_testing_endpoints import router as ab_testing_router

# Existing imports
from app.api import recommendations, interactions, health
from app.core import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global instances
redis_client = None
cold_start_handler = None
ab_framework = None
strategy_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global redis_client, cold_start_handler, ab_framework, strategy_manager
    
    # Startup
    logger.info("Starting ML Service with Phase 3 features...")
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True
    )
    
    # Initialize Phase 3 components
    cold_start_handler = ColdStartHandler(redis_client)
    ab_framework = ABTestingFramework(redis_client)
    strategy_manager = StrategyManager(redis_client)
    
    logger.info("Phase 3 components initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML Service...")
    if redis_client:
        redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="ML Recommendation Service",
    version="3.0.0",
    description="Real-time recommendation engine with A/B testing and cold start handling",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routers
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(interactions.router, prefix="/interactions", tags=["Interactions"])
app.include_router(health.router, prefix="/health", tags=["Health"])

# Include Phase 3 routers
app.include_router(ab_testing_router, prefix="/experiments", tags=["A/B Testing"])

# Cold Start Endpoints
class ColdStartRequest(BaseModel):
    user_id: str
    demographics: Optional[Dict] = None
    strategy: str = "hybrid"
    limit: int = 10

class ColdStartItemRequest(BaseModel):
    item_id: str
    item_features: Dict
    limit: int = 10

@app.post("/recommendations/cold-start")
async def get_cold_start_recommendations(request: ColdStartRequest):
    """Get recommendations for new user (cold start)"""
    
    demographics = None
    if request.demographics:
        demographics = UserDemographics(
            age_group=request.demographics.get("age_group"),
            gender=request.demographics.get("gender"),
            location=request.demographics.get("location"),
            interests=request.demographics.get("interests", []),
            registration_date=request.demographics.get("registration_date", "")
        )
    
    recommendations = cold_start_handler.get_recommendations_for_new_user(
        user_id=request.user_id,
        demographics=demographics,
        limit=request.limit,
        strategy=request.strategy
    )
    
    return {
        "user_id": request.user_id,
        "recommendations": recommendations,
        "strategy": request.strategy,
        "type": "cold_start"
    }

@app.post("/recommendations/cold-start/item")
async def get_cold_start_item_targets(request: ColdStartItemRequest):
    """Get target users for new item (cold start)"""
    
    target_users = cold_start_handler.get_recommendations_for_new_item(
        item_id=request.item_id,
        item_features=request.item_features,
        limit=request.limit
    )
    
    return {
        "item_id": request.item_id,
        "target_users": target_users,
        "count": len(target_users)
    }

# A/B Tested Recommendations
@app.get("/recommendations/ab-tested/{user_id}")
async def get_ab_tested_recommendations(
    user_id: str,
    limit: int = 10,
    experiment_id: Optional[str] = None
):
    """Get recommendations with A/B testing applied"""
    
    result = strategy_manager.get_recommendations(
        user_id=user_id,
        experiment_id=experiment_id,
        limit=limit
    )
    
    return result

# Trending Items (from stream processor)
@app.get("/recommendations/trending")
async def get_trending_items(limit: int = 20):
    """Get current trending items"""
    
    trending = redis_client.get("trending_items")
    if trending:
        import json
        items = json.loads(trending)
        return {
            "items": items[:limit],
            "timestamp": None,
            "source": "stream_processor"
        }
    
    return {
        "items": [],
        "message": "No trending data available"
    }

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def get_metrics():
    """Export metrics for Prometheus"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "ML Recommendation Service",
        "version": "3.0.0",
        "features": [
            "Collaborative Filtering",
            "Content-Based Filtering",
            "Hybrid Recommendations",
            "Cold Start Handling",
            "A/B Testing Framework",
            "Real-time Stream Processing",
            "Advanced Caching"
        ],
        "endpoints": {
            "recommendations": "/recommendations",
            "cold_start": "/recommendations/cold-start",
            "experiments": "/experiments",
            "trending": "/recommendations/trending",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)