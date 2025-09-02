// config.rs
use serde::Deserialize;
use config::{Config, Environment};

#[derive(Debug, Deserialize, Clone)]
pub struct AppConfig {
    pub host: String,
    pub port: u16,
    pub redis_url: String,
    pub log_level: String,
    pub max_connections: usize,
    pub cache_default_ttl: u64,
}

impl AppConfig {
    pub fn from_env() -> anyhow::Result<Self> {
        dotenv::dotenv().ok();
        
        let config = Config::builder()
            .set_default("host", "0.0.0.0")?
            .set_default("port", 8082)?
            .set_default("redis_url", "redis://redis:6379")?
            .set_default("log_level", "info")?
            .set_default("max_connections", 50)?
            .set_default("cache_default_ttl", 3600)?
            .add_source(Environment::with_prefix("CACHE_SERVICE"))
            .build()?;
        
        Ok(config.try_deserialize()?)
    }
}