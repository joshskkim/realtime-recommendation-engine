"""
Configuration for ML Service
File: services/ml-service/app/core/config.py
"""

import os
from typing import Optional

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_INTERACTIONS = os.getenv("KAFKA_TOPIC_INTERACTIONS", "user-interactions")
KAFKA_TOPIC_RECOMMENDATIONS = os.getenv("KAFKA_TOPIC_RECOMMENDATIONS", "recommendations-generated")
KAFKA_TOPIC_EVENTS = os.getenv("KAFKA_TOPIC_EVENTS", "system-events")

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "userdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# ML Model Configuration
MODEL_UPDATE_INTERVAL = int(os.getenv("MODEL_UPDATE_INTERVAL", 3600))
MIN_INTERACTIONS_FOR_CF = int(os.getenv("MIN_INTERACTIONS_FOR_CF", 5))
CONTENT_SIMILARITY_THRESHOLD = float(os.getenv("CONTENT_SIMILARITY_THRESHOLD", 0.1))

# Recommendation Configuration
DEFAULT_RECOMMENDATION_COUNT = int(os.getenv("DEFAULT_RECOMMENDATION_COUNT", 10))
MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", 50))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))

# Service Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "ml-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")