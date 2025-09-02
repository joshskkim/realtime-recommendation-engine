"""
User interaction API endpoints
File: services/ml-service/app/api/interactions.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import json
import redis
from kafka import KafkaProducer
from app.core import config

router = APIRouter()

# Initialize connections
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True
)

kafka_producer = KafkaProducer(
    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class InteractionRequest(BaseModel):
    user_id: str
    item_id: str
    interaction_type: str  # view, click, purchase, like, rating
    rating: Optional[float] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict] = None

class InteractionResponse(BaseModel):
    success: bool
    message: str
    interaction_id: Optional[str] = None

@router.post("/")
async def record_interaction(interaction: InteractionRequest) -> InteractionResponse:
    """Record a user interaction"""
    
    # Validate interaction type
    valid_types = ["view", "click", "purchase", "like", "rating", "add_to_cart"]
    if interaction.interaction_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interaction type. Must be one of: {valid_types}"
        )
    
    # Create interaction event
    event = {
        "user_id": interaction.user_id,
        "item_id": interaction.item_id,
        "interaction_type": interaction.interaction_type,
        "rating": interaction.rating,
        "session_id": interaction.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": interaction.metadata
    }
    
    # Send to Kafka for stream processing
    try:
        kafka_producer.send(
            config.KAFKA_TOPIC_INTERACTIONS,
            value=event
        )
        kafka_producer.flush()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send to Kafka: {str(e)}"
        )
    
    # Update user's recent interactions in Redis
    user_key = f"user_interactions:{interaction.user_id}"
    redis_client.lpush(user_key, json.dumps(event))
    redis_client.ltrim(user_key, 0, 99)  # Keep last 100 interactions
    redis_client.expire(user_key, 86400)  # 24 hour expiry
    
    # Invalidate recommendation cache for the user
    cache_key = f"recommendations:{interaction.user_id}"
    redis_client.delete(cache_key)
    
    # Update item interaction count
    item_key = f"item_interactions:{interaction.item_id}"
    redis_client.hincrby(item_key, interaction.interaction_type, 1)
    
    return InteractionResponse(
        success=True,
        message="Interaction recorded successfully",
        interaction_id=f"{interaction.user_id}_{interaction.item_id}_{datetime.utcnow().timestamp()}"
    )

@router.get("/user/{user_id}")
async def get_user_interactions(
    user_id: str,
    limit: int = 20
) -> Dict:
    """Get recent interactions for a user"""
    
    user_key = f"user_interactions:{user_id}"
    interactions = redis_client.lrange(user_key, 0, limit - 1)
    
    return {
        "user_id": user_id,
        "interactions": [json.loads(i) for i in interactions],
        "count": len(interactions)
    }

@router.get("/item/{item_id}/stats")
async def get_item_interaction_stats(item_id: str) -> Dict:
    """Get interaction statistics for an item"""
    
    item_key = f"item_interactions:{item_id}"
    stats = redis_client.hgetall(item_key)
    
    # Convert string values to integers
    stats = {k: int(v) for k, v in stats.items()}
    
    # Calculate engagement score
    engagement_score = (
        stats.get("view", 0) * 1 +
        stats.get("click", 0) * 2 +
        stats.get("like", 0) * 3 +
        stats.get("add_to_cart", 0) * 4 +
        stats.get("purchase", 0) * 5
    )
    
    return {
        "item_id": item_id,
        "stats": stats,
        "engagement_score": engagement_score,
        "total_interactions": sum(stats.values())
    }

@router.post("/batch")
async def record_batch_interactions(interactions: list[InteractionRequest]) -> Dict:
    """Record multiple interactions at once"""
    
    if len(interactions) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 1000 interactions per batch"
        )
    
    success_count = 0
    failed_count = 0
    
    for interaction in interactions:
        try:
            event = {
                "user_id": interaction.user_id,
                "item_id": interaction.item_id,
                "interaction_type": interaction.interaction_type,
                "rating": interaction.rating,
                "session_id": interaction.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": interaction.metadata
            }
            
            kafka_producer.send(
                config.KAFKA_TOPIC_INTERACTIONS,
                value=event
            )
            success_count += 1
        except:
            failed_count += 1
    
    kafka_producer.flush()
    
    return {
        "total": len(interactions),
        "success": success_count,
        "failed": failed_count
    }