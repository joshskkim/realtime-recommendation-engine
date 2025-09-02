// Rust Datadog integration
use dogstatsd::{Client, Options};

pub struct DatadogMetrics {
    client: Client,
}

impl DatadogMetrics {
    pub fn new() -> Self {
        let options = Options::new("datadog-agent", "8125");
        let client = Client::new(options).unwrap();
        
        DatadogMetrics { client }
    }
    
    pub fn track_cache_hit(&self) {
        self.client.incr("cache.hits", 1).unwrap();
    }
    
    pub fn track_cache_miss(&self) {
        self.client.incr("cache.misses", 1).unwrap();
    }
    
    pub fn track_latency(&self, duration: f64) {
        self.client.histogram("cache.latency", duration).unwrap();
    }
}