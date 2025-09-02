use deadpool_redis::{redis::AsyncCommands, Connection, Pool};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{debug, info};

use crate::error::Result;
use crate::{metrics::Metrics};

#[derive(Debug, Clone)]
pub enum CacheStrategy {
    Standard,      // Basic get/set
    LRU,          // Least Recently Used
    LFU,          // Least Frequently Used
    WriteThrough, // Write to cache and backing store
    WriteBack,    // Write to cache, async write to backing store
}

impl CacheStrategy {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "lru" => Self::LRU,
            "lfu" => Self::LFU,
            "write_through" => Self::WriteThrough,
            "write_back" => Self::WriteBack,
            _ => Self::Standard,
        }
    }
}

#[derive(Clone)]
pub struct CacheManager {
    pool: Pool,
    metrics: Arc<Metrics>,
}

impl CacheManager {
    pub fn new(pool: Pool, metrics: Arc<Metrics>) -> Self {
        Self { pool, metrics }
    }

    pub async fn ping(&self) -> Result<()> {
        let mut conn = self.pool.get().await?;
        let pong: String = redis::cmd("PING")
            .query_async(&mut conn)
            .await?;
        assert_eq!(pong, "PONG");
        Ok(())
    }

    pub async fn get(&self, key: &str, strategy: CacheStrategy) -> Result<Option<Value>> {
        let mut conn = self.pool.get().await?;
        
        // Record access for LRU/LFU strategies
        match strategy {
            CacheStrategy::LRU => {
                self.update_access_time(key, &mut conn).await?;
            }
            CacheStrategy::LFU => {
                self.increment_access_count(key, &mut conn).await?;
            }
            _ => {}
        }

        let data: Option<String> = conn.get(key).await?;
        
        match data {
            Some(json_str) => {
                let value: Value = serde_json::from_str(&json_str)?;
                debug!("Cache hit for key: {}", key);
                Ok(Some(value.into()))
            }
            None => {
                debug!("Cache miss for key: {}", key);
                Ok(None)
            }
        }
    }

    pub async fn set(
        &self,
        key: &str,
        value: Value,
        ttl: u64,
        strategy: CacheStrategy,
    ) -> Result<()> {
        let mut conn = self.pool.get().await?;
        let json_str = serde_json::to_string(&value)?;
        
        match strategy {
            CacheStrategy::WriteThrough => {
                // Write to cache
                conn.set_ex::<&str, &str, ()>(key, &json_str, ttl).await?;
                // In production, would also write to backing store
                self.write_to_backing_store(key).await?;
            }
            CacheStrategy::WriteBack => {
                // Write to cache immediately
                conn.set_ex::<&str, &str, ()>(key, &json_str, ttl).await?;
                // Queue for async write to backing store
                self.queue_write_back(key).await?;
            }
            _ => {
                // Standard write
                conn.set_ex::<&str, &str, ()>(key, &json_str, ttl).await?;
            }
        }
        
        // Update metadata for eviction strategies
        match strategy {
            CacheStrategy::LRU => {
                self.update_access_time(key, &mut conn).await?;
            }
            CacheStrategy::LFU => {
                self.reset_access_count(key, &mut conn).await?;
            }
            _ => {}
        }
        
        debug!("Set cache key: {} with TTL: {}s", key, ttl);
        Ok(())
    }

    pub async fn delete(&self, key: &str) -> Result<()> {
        let mut conn = self.pool.get().await?;
        conn.del::<&str, ()>(key).await?;
        
        // Clean up metadata
        self.delete_metadata(key, &mut conn).await?;
        
        debug!("Deleted cache key: {}", key);
        Ok(())
    }

    pub async fn invalidate_by_tag(&self, tag: &str) -> Result<()> {
        let mut conn = self.pool.get().await?;
        
        // Get all keys with this tag
        let pattern = format!("tag:{}:*", tag);
        let keys: Vec<String> = conn.keys(&pattern).await?;
        
        if !keys.is_empty() {
            // Delete all keys with this tag
            for key in &keys {
                conn.del::<&str, ()>(key).await?;
            }
            info!("Invalidated {} keys with tag: {}", keys.len(), tag);
        }
        
        Ok(())
    }

    pub async fn get_stats(&self) -> Result<Value> {
        let mut conn = self.pool.get().await?;
        
        // Get Redis info
        let info: String = redis::cmd("INFO")
            .arg("stats")
            .query_async(&mut conn)
            .await?;
        
        // Parse key statistics
        let db_size: i64 = redis::cmd("DBSIZE").query_async(&mut conn).await?;
        
        // Get memory info
        let memory_info: String = redis::cmd("INFO")
            .arg("memory")
            .query_async(&mut conn)
            .await?;
        
        // Parse and structure the stats
        let stats = serde_json::json!({
            "total_keys": db_size,
            "redis_info": parse_redis_info(&info),
            "memory": parse_redis_info(&memory_info),
            "metrics": {
                "hits": self.metrics.get_hits(),
                "misses": self.metrics.get_misses(),
                "hit_rate": self.metrics.get_hit_rate(),
            }
        });
        
        Ok(stats)
    }

    pub async fn warm_cache(&self, key: &str) -> Result<()> {
        // In production, would fetch from primary data source
        // For now, simulate warming with dummy data
        let dummy_data = serde_json::json!({
            "warmed": true,
            "timestamp": SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        });
        
        self.set(key, dummy_data, 3600, CacheStrategy::Standard).await?;
        info!("Warmed cache for key: {}", key);
        Ok(())
    }

    // Helper methods for LRU strategy
    async fn update_access_time(&self, key: &str, conn: &mut Connection) -> Result<()> {
        let access_key = format!("access:time:{}", key);
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        conn.set_ex::<&str, u64, ()>(&access_key, timestamp, 86400).await?;
        Ok(())
    }

    // Helper methods for LFU strategy
    async fn increment_access_count(&self, key: &str, conn: &mut Connection) -> Result<()> {
        let count_key = format!("access:count:{}", key);
        // Specify all three generic parameters: key type, value type, return type
        let _: u64 = conn.incr::<&str, u64, u64>(&count_key, 1).await?;
        // Explicitly annotate the return type as unit `()`
        let _: u64 = conn.expire::<&str, u64>(&count_key, 86400).await?;
        Ok(())
    }

    async fn reset_access_count(&self, key: &str, conn: &mut Connection) -> Result<()> {
        let count_key = format!("access:count:{}", key);
        conn.set_ex::<&str, u64, ()>(&count_key, 1, 86400).await?;
        Ok(())
    }

    async fn delete_metadata(&self, key: &str, conn: &mut Connection) -> Result<()> {
        let time_key = format!("access:time:{}", key);
        let count_key = format!("access:count:{}", key);
        conn.del::<&str, ()>(&time_key).await?;
        conn.del::<&str, ()>(&count_key).await?;
        Ok(())
    }

    async fn write_to_backing_store(&self, key: &str) -> Result<()> {
        // In production, would write to PostgreSQL or other backing store
        debug!("Write-through to backing store for key: {}", key);
        Ok(())
    }

    async fn queue_write_back(&self, key: &str) -> Result<()> {
        // In production, would queue to Kafka for async processing
        debug!("Queued write-back for key: {}", key);
        Ok(())
    }
}

fn parse_redis_info(info: &str) -> HashMap<String, String> {
    let mut result = HashMap::new();
    
    for line in info.lines() {
        if line.contains(':') && !line.starts_with('#') {
            let parts: Vec<&str> = line.split(':').collect();
            if parts.len() == 2 {
                result.insert(
                    parts[0].to_string(),
                    parts[1].trim().to_string(),
                );
            }
        }
    }
    
    result
}