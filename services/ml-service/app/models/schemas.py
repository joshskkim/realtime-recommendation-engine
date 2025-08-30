"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class InteractionType(str, Enum):
    """Valid interaction types"""
    VIEW = "view"
    LIKE = "like"
    DISLIKE = "dislike"
    SHARE = "share"
    PURCHASE = "purchase"
    RATING = "rating"


class Algorithm(str, Enum):
    """Available recommendation algorithms"""
    HYBRID = "hybrid"
    COLLABORATIVE = "collaborative"
    CONTENT = "content"
    POPULARITY = "popularity"


# Base schemas
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str
    redis_connected: bool
    model_trained: bool


# Interaction schemas
class InteractionRequest(BaseModel):
    """Request model for recording user interactions"""
    user_id: int = Field(..., gt=0, description="User ID")
    item_id: int = Field(..., gt=0, description="Item ID")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Rating (1-5)")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    @validator('rating')
    def validate_rating(cls, v, values):
        if values.get('interaction_type') == InteractionType.RATING and v is None:
            raise ValueError('Rating is required for rating interactions')
        return v


class UserInteraction(BaseModel):
    """User interaction model"""
    interaction_id: int
    user_id: int
    item_id: int
    interaction_type: str
    rating: Optional[float]
    session_id: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Recommendation schemas
class RecommendationRequest(BaseModel):
    """Request model for getting recommendations"""
    user_id: int = Field(..., gt=0, description="User ID")
    limit: int = Field(10, gt=0, le=100, description="Number of recommendations")
    algorithm: Algorithm = Field(Algorithm.HYBRID, description="Recommendation algorithm")
    exclude_seen: bool = Field(True, description="Exclude items user has already seen")


class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    item_id: int
    title: str
    category: Optional[str]
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score")
    algorithm: str
    explanation: str
    metadata: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    """Response model for user recommendations"""
    user_id: int
    recommendations: List[RecommendationItem]
    algorithm: str
    timestamp: str
    cached: bool = Field(False, description="Whether results came from cache")
    total_available: Optional[int] = Field(None, description="Total recommendations available")


# Similar items schemas
class SimilarItemsResponse(BaseModel):
    """Response model for similar items"""
    item_id: int
    similar_items: List[RecommendationItem]
    timestamp: str


# User and Item schemas
class UserBase(BaseModel):
    """Base user schema"""
    age_group: Optional[str]
    preferred_categories: List[str] = []
    is_premium: bool = False
    location: Optional[str]


class UserCreate(UserBase):
    """Schema for creating a user"""
    pass


class UserResponse(UserBase):
    """Response schema for user"""
    user_id: int
    registration_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ItemBase(BaseModel):
    """Base item schema"""
    title: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    features: Dict[str, Any] = {}


class ItemCreate(ItemBase):
    """Schema for creating an item"""
    pass


class ItemResponse(ItemBase):
    """Response schema for item"""
    item_id: int
    created_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Model and system schemas
class ModelStats(BaseModel):
    """Model statistics response"""
    is_trained: bool
    last_training: Optional[str]
    cf_users: int
    cf_items: int
    hybrid_weights: Dict[str, float]
    training_data_size: Optional[int] = None


class CacheStats(BaseModel):
    """Cache statistics response"""
    connected_clients: int
    used_memory: str
    keyspace_hits: int
    keyspace_misses: int
    hit_rate: float


# Bulk operation schemas
class BulkInteractionRequest(BaseModel):
    """Bulk interaction upload"""
    interactions: List[InteractionRequest] = Field(..., max_items=1000)


class BulkRecommendationRequest(BaseModel):
    """Bulk recommendation request"""
    user_ids: List[int] = Field(..., max_items=100)
    limit: int = Field(10, gt=0, le=50)
    algorithm: Algorithm = Field(Algorithm.HYBRID)


class BulkRecommendationResponse(BaseModel):
    """Bulk recommendation response"""
    recommendations: Dict[int, List[RecommendationItem]]
    algorithm: str
    timestamp: str
    processed_users: int
    failed_users: List[int] = []


# Error schemas
class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None


# Analytics schemas
class UserAnalytics(BaseModel):
    """User analytics response"""
    user_id: int
    total_interactions: int
    avg_rating: Optional[float]
    favorite_categories: List[str]
    last_activity: Optional[datetime]
    recommendation_diversity: Optional[float]


class ItemAnalytics(BaseModel):
    """Item analytics response"""
    item_id: int
    total_interactions: int
    avg_rating: Optional[float]
    popularity_score: float
    recommendation_frequency: int


class SystemAnalytics(BaseModel):
    """System-wide analytics"""
    total_users: int
    total_items: int
    total_interactions: int
    active_users_30d: int
    top_categories: List[Dict[str, Any]]
    recommendation_stats: Dict[str, int]
    timestamp: str


# Configuration schemas
class HybridWeights(BaseModel):
    """Hybrid algorithm weights configuration"""
    collaborative: float = Field(..., ge=0.0, le=1.0)
    content_based: float = Field(..., ge=0.0, le=1.0)
    popularity: float = Field(..., ge=0.0, le=1.0)
    
    @validator('popularity')
    def weights_sum_to_one(cls, v, values):
        total = v + values.get('collaborative', 0) + values.get('content_based', 0)
        if abs(total - 1.0) > 0.01:
            raise ValueError('Weights must sum to 1.0')
        return v


class ModelConfig(BaseModel):
    """Model configuration"""
    n_factors: int = Field(50, gt=0, le=200)
    min_interactions: int = Field(5, gt=0)
    hybrid_weights: HybridWeights
    retrain_interval_hours: int = Field(24, gt=0)


# A/B Testing schemas
class ABTestConfig(BaseModel):
    """A/B test configuration"""
    test_name: str
    control_algorithm: Algorithm
    test_algorithm: Algorithm
    traffic_split: float = Field(0.5, ge=0.1, le=0.9)
    start_date: datetime
    end_date: datetime


class ABTestResult(BaseModel):
    """A/B test results"""
    test_name: str
    control_ctr: float
    test_ctr: float
    confidence: float
    winner: str
    sample_size: int