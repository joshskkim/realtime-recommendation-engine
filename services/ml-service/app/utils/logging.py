"""
Logging configuration for the ML service
"""

import logging
import sys
import os
from typing import Optional
import structlog
from datetime import datetime


def setup_logging(level: Optional[str] = None) -> structlog.BoundLogger:
    """
    Setup structured logging with appropriate configuration
    """
    
    # Get log level from environment or use provided level
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.INFO),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.processors.TimeStamper(fmt="ISO"),
            # Add log level
            structlog.processors.add_log_level,
            # Add logger name
            structlog.processors.add_logger_name,
            # Stack info processor
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            # JSON formatter for production, console for development
            _get_log_renderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create and return logger
    logger = structlog.get_logger("ml-service")
    logger.info("Logging configured", level=log_level)
    
    return logger


def _get_log_renderer():
    """
    Get appropriate log renderer based on environment
    """
    env = os.getenv("ENVIRONMENT", "development")
    structured_logging = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"
    
    if env == "production" or structured_logging:
        return structlog.processors.JSONRenderer()
    else:
        return structlog.dev.ConsoleRenderer(colors=True)


class RequestLogger:
    """
    Middleware for logging HTTP requests
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    async def log_request(self, request, call_next):
        """Log incoming HTTP requests"""
        start_time = datetime.now()
        
        # Log request
        self.logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log response
        self.logger.info(
            "HTTP request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_seconds=duration,
        )
        
        return response


class RecommendationLogger:
    """
    Specialized logger for recommendation events
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger.bind(component="recommendations")
    
    def log_recommendation_request(self, user_id: int, algorithm: str, limit: int):
        """Log recommendation request"""
        self.logger.info(
            "Recommendation request",
            user_id=user_id,
            algorithm=algorithm,
            limit=limit,
            event_type="recommendation_request"
        )
    
    def log_recommendation_response(self, user_id: int, algorithm: str, 
                                  count: int, cached: bool, duration_ms: float):
        """Log recommendation response"""
        self.logger.info(
            "Recommendation response",
            user_id=user_id,
            algorithm=algorithm,
            recommendation_count=count,
            cached=cached,
            duration_ms=duration_ms,
            event_type="recommendation_response"
        )
    
    def log_interaction_recorded(self, user_id: int, item_id: int, 
                               interaction_type: str, rating: Optional[float] = None):
        """Log user interaction"""
        self.logger.info(
            "Interaction recorded",
            user_id=user_id,
            item_id=item_id,
            interaction_type=interaction_type,
            rating=rating,
            event_type="interaction_recorded"
        )
    
    def log_model_training_start(self, interaction_count: int):
        """Log model training start"""
        self.logger.info(
            "Model training started",
            interaction_count=interaction_count,
            event_type="model_training_start"
        )
    
    def log_model_training_complete(self, duration_seconds: float, 
                                  users_count: int, items_count: int):
        """Log model training completion"""
        self.logger.info(
            "Model training completed",
            duration_seconds=duration_seconds,
            users_count=users_count,
            items_count=items_count,
            event_type="model_training_complete"
        )
    
    def log_cache_hit(self, cache_key: str, user_id: Optional[int] = None):
        """Log cache hit"""
        self.logger.debug(
            "Cache hit",
            cache_key=cache_key,
            user_id=user_id,
            event_type="cache_hit"
        )
    
    def log_cache_miss(self, cache_key: str, user_id: Optional[int] = None):
        """Log cache miss"""
        self.logger.debug(
            "Cache miss",
            cache_key=cache_key,
            user_id=user_id,
            event_type="cache_miss"
        )


class PerformanceLogger:
    """
    Logger for performance metrics
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger.bind(component="performance")
    
    def log_algorithm_performance(self, algorithm: str, execution_time_ms: float, 
                                 user_count: int, item_count: int):
        """Log algorithm performance metrics"""
        self.logger.info(
            "Algorithm performance",
            algorithm=algorithm,
            execution_time_ms=execution_time_ms,
            user_count=user_count,
            item_count=item_count,
            event_type="algorithm_performance"
        )
    
    def log_database_query_performance(self, query_type: str, execution_time_ms: float, 
                                     record_count: Optional[int] = None):
        """Log database query performance"""
        self.logger.debug(
            "Database query performance",
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            record_count=record_count,
            event_type="database_performance"
        )
    
    def log_cache_performance(self, operation: str, execution_time_ms: float, 
                            hit_rate: Optional[float] = None):
        """Log cache performance metrics"""
        self.logger.debug(
            "Cache performance",
            operation=operation,
            execution_time_ms=execution_time_ms,
            hit_rate=hit_rate,
            event_type="cache_performance"
        )