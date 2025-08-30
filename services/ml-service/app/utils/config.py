"""
Configuration management for the ML service
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    service_name: str = Field("ml-service", env="SERVICE_NAME")
    service_version: str = Field("1.0.0", env="SERVICE_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="ML_SERVICE_DEBUG")
    
    # Database Configuration
    database_url: str = Field(
        "postgresql://recuser:recpass123@postgres:5432/recommendations",
        env="DATABASE_URL"
    )
    db_echo: bool = Field(False, env="DB_ECHO")
    
    # Redis Configuration
    redis_url: str = Field("redis://redis:6379", env="REDIS_URL")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # Cache TTL Settings (seconds)
    cache_ttl_user_profile: int = Field(3600, env="CACHE_TTL_USER_PROFILE")
    cache_ttl_recommendations: int = Field(1800, env="CACHE_TTL_RECOMMENDATIONS")
    cache_ttl_item_features: int = Field(7200, env="CACHE_TTL_ITEM_FEATURES")
    cache_ttl_popularity: int = Field(600, env="CACHE_TTL_POPULARITY")
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field("kafka:29092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_client_id: str = Field("ml-service", env="KAFKA_CLIENT_ID")
    kafka_group_id: str = Field("ml-service-consumers", env="KAFKA_GROUP_ID")
    
    # Kafka Topics
    kafka_topic_user_interactions: str = Field("user-interactions", env="KAFKA_TOPIC_USER_INTERACTIONS")
    kafka_topic_recommendations: str = Field("recommendations-generated", env="KAFKA_TOPIC_RECOMMENDATIONS")
    kafka_topic_model_updates: str = Field("model-updates", env="KAFKA_TOPIC_MODEL_UPDATES")
    kafka_topic_system_events: str = Field("system-events", env="KAFKA_TOPIC_SYSTEM_EVENTS")
    
    # ML Model Configuration
    model_update_interval: int = Field(3600, env="MODEL_UPDATE_INTERVAL")  # seconds
    min_interactions_for_cf: int = Field(5, env="MIN_INTERACTIONS_FOR_CF")
    content_similarity_threshold: float = Field(0.1, env="CONTENT_SIMILARITY_THRESHOLD")
    
    # Hybrid Algorithm Weights
    hybrid_weights_cf: float = Field(0.4, env="HYBRID_WEIGHTS_CF")
    hybrid_weights_cb: float = Field(0.4, env="HYBRID_WEIGHTS_CB")
    hybrid_weights_popularity: float = Field(0.2, env="HYBRID_WEIGHTS_POPULARITY")
    
    # Cold Start Configuration
    cold_start_min_popular_items: int = Field(20, env="COLD_START_MIN_POPULAR_ITEMS")
    cold_start_demographic_weight: float = Field(0.6, env="COLD_START_DEMOGRAPHIC_WEIGHT")
    
    # API Configuration
    max_recommendations_per_request: int = Field(50, env="MAX_RECOMMENDATIONS_PER_REQUEST")
    default_recommendations_count: int = Field(10, env="DEFAULT_RECOMMENDATIONS_COUNT")
    enable_explanation: bool = Field(True, env="ENABLE_EXPLANATION")
    enable_ab_testing: bool = Field(True, env="ENABLE_AB_TESTING")
    
    # Security Configuration
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    internal_api_key: str = Field("internal-service-key", env="INTERNAL_API_KEY")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(True, env="STRUCTURED_LOGGING")
    
    # Development Configuration
    enable_debug_endpoints: bool = Field(True, env="ENABLE_DEBUG_ENDPOINTS")
    sample_data_size: int = Field(1000, env="SAMPLE_DATA_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def hybrid_weights(self) -> Dict[str, float]:
        """Get normalized hybrid algorithm weights"""
        weights = {
            "collaborative": self.hybrid_weights_cf,
            "content_based": self.hybrid_weights_cb,
            "popularity": self.hybrid_weights_popularity
        }
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    @property
    def kafka_topics(self) -> Dict[str, str]:
        """Get all Kafka topic names"""
        return {
            "user_interactions": self.kafka_topic_user_interactions,
            "recommendations": self.kafka_topic_recommendations,
            "model_updates": self.kafka_topic_model_updates,
            "system_events": self.kafka_topic_system_events
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()