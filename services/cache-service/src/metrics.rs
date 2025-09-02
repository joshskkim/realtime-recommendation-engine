
// metrics.rs
use prometheus::{Histogram, HistogramOpts, IntCounter, IntGauge};

pub struct Metrics {
    cache_hits: IntCounter,
    cache_misses: IntCounter,
    cache_requests: IntCounter,
    cache_latency: Histogram,
    connection_pool_size: IntGauge,
}

impl Metrics {
    pub fn new() -> Self {
        let cache_hits = IntCounter::new("cache_hits_total", "Total cache hits")
            .expect("metric creation");
        let cache_misses = IntCounter::new("cache_misses_total", "Total cache misses")
            .expect("metric creation");
        let cache_requests = IntCounter::new("cache_requests_total", "Total cache requests")
            .expect("metric creation");
        
        let latency_opts = HistogramOpts::new("cache_latency_seconds", "Cache operation latency");
        let cache_latency = Histogram::with_opts(latency_opts).expect("metric creation");
        
        let connection_pool_size = IntGauge::new("connection_pool_size", "Redis connection pool size")
            .expect("metric creation");
        
        // Register metrics
        prometheus::register(Box::new(cache_hits.clone())).ok();
        prometheus::register(Box::new(cache_misses.clone())).ok();
        prometheus::register(Box::new(cache_requests.clone())).ok();
        prometheus::register(Box::new(cache_latency.clone())).ok();
        prometheus::register(Box::new(connection_pool_size.clone())).ok();
        
        Self {
            cache_hits,
            cache_misses,
            cache_requests,
            cache_latency,
            connection_pool_size,
        }
    }
    
    pub fn cache_hit(&self) {
        self.cache_hits.inc();
    }
    
    pub fn cache_miss(&self) {
        self.cache_misses.inc();
    }

    pub fn cache_request(&self, _operation: &str) {
        self.cache_requests.inc();
    }
    
    pub fn get_hits(&self) -> u64 {
        self.cache_hits.get()
    }
    
    pub fn get_misses(&self) -> u64 {
        self.cache_misses.get()
    }
    
    pub fn get_hit_rate(&self) -> f64 {
        let hits = self.cache_hits.get() as f64;
        let total = (self.cache_hits.get() + self.cache_misses.get()) as f64;
        if total > 0.0 {
            hits / total
        } else {
            0.0
        }
    }
}