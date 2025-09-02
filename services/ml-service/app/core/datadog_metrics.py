from datadog import initialize, statsd
import time
from functools import wraps

# Initialize Datadog
options = {
    'statsd_host': 'datadog-agent',
    'statsd_port': 8125
}
initialize(**options)

def track_recommendation_metrics(func):
    """Decorator to track recommendation metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Track success metrics
            statsd.increment('recommendations.generated', 
                           tags=[f'strategy:{kwargs.get("strategy", "unknown")}'])
            statsd.histogram('recommendations.latency', 
                           time.time() - start_time,
                           tags=[f'strategy:{kwargs.get("strategy", "unknown")}'])
            
            return result
        except Exception as e:
            # Track error metrics
            statsd.increment('recommendations.errors',
                           tags=[f'error:{type(e).__name__}'])
            raise
    
    return wrapper