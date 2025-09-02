"""
Health check endpoints
File: services/ml-service/app/api/health.py
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import redis
import psycopg2
from kafka import KafkaProducer
import time
from app.core import config

router = APIRouter()

@router.get("/")
async def health_check() -> Dict:
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "ml-service",
        "timestamp": int(time.time())
    }

@router.get("/ready")
async def readiness_check() -> Dict:
    """Check if service is ready to accept requests"""
    checks = {
        "redis": False,
        "postgres": False,
        "kafka": False
    }
    
    # Check Redis
    try:
        r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
        r.ping()
        checks["redis"] = True
    except:
        pass
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD
        )
        conn.close()
        checks["postgres"] = True
    except:
        pass
    
    # Check Kafka
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=2000
        )
        producer.close()
        checks["kafka"] = True
    except:
        pass
    
    all_healthy = all(checks.values())
    
    if not all_healthy:
        raise HTTPException(status_code=503, detail=checks)
    
    return {
        "status": "ready",
        "checks": checks
    }

@router.get("/live")
async def liveness_check() -> Dict:
    """Check if service is alive"""
    return {"status": "alive"}