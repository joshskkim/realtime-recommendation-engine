use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Serialize, Deserialize, Debug)]
pub struct RecommendationCache {
    pub user_id: String,
    pub items: Vec<String>,
}

#[derive(Error, Debug)]
pub enum CacheError {
    #[error("Redis error: {0}")]
    RedisError(#[from] redis::RedisError),
    #[error("Serialization error: {0}")]
    SerdeError(#[from] serde_json::Error),
}

pub struct CacheStore {
    client: redis::Client,
}

impl CacheStore {
    pub fn new(url: &str) -> Result<Self, CacheError> {
        Ok(Self {
            client: redis::Client::open(url)?,
        })
    }

    pub async fn get(&self, user_id: &str) -> Result<Option<RecommendationCache>, CacheError> {
        let mut conn = self.client.get_async_connection().await?;
        let raw: Option<String> = conn.get(user_id).await?;
        if let Some(json_str) = raw {
            let cache: RecommendationCache = serde_json::from_str(&json_str)?;
            Ok(Some(cache))
        } else {
            Ok(None)
        }
    }

    pub async fn set(
        &self,
        cache: &RecommendationCache,
    ) -> Result<(), CacheError> {
        let mut conn = self.client.get_async_connection().await?;
        let payload = serde_json::to_string(cache)?;
        // avoid the `never`‐type fallback warning by explicitly specifying `()` as the command’s return
        conn.set::<_, _, ()>(&cache.user_id, payload).await?;
        Ok(())
    }
}
