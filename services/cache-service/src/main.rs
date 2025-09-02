use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::Json,
    routing::{delete, get, post, put},
    Router,
};
use deadpool_redis::{Config as RedisConfig, Runtime};
use prometheus::{Encoder, TextEncoder};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::Arc};
use tower_http::cors::CorsLayer;
use tracing::{error, info};

mod cache;
mod config;
mod error;
mod metrics;

use crate::{
    cache::{CacheManager, CacheStrategy},
    config::AppConfig,
    error::{AppError, Result},
    metrics::Metrics,
};

#[derive(Clone)]
struct AppState {
    cache: Arc<CacheManager>,
    metrics: Arc<Metrics>,
    config: Arc<AppConfig>,
}

#[derive(Serialize, Deserialize)]
struct CacheEntry {
    key: String,
    value: serde_json::Value,
    ttl: Option<u64>,
    tags: Option<Vec<String>>,
}

#[derive(Serialize, Deserialize)]
struct BatchCacheRequest {
    entries: Vec<CacheEntry>,
    strategy: Option<String>,
}

#[derive(Deserialize)]
struct CacheParams {
    strategy: Option<String>,
    ttl: Option<u64>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    version: String,
    redis_connected: bool,
    uptime_seconds: u64,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("cache_service=info".parse()?),
        )
        .init();

    info!("Starting Rust Cache Service");

    // Load configuration
    let config = Arc::new(AppConfig::from_env()?);

    // Initialize Redis pool
    let redis_cfg = RedisConfig {
        url: Some(config.redis_url.clone()),
        pool: Some(deadpool_redis::PoolConfig {
            max_size: config.max_connections,
            ..Default::default()
        }),
        connection: None,
    };
    
    let redis_pool = redis_cfg.create_pool(Some(Runtime::Tokio1))?;

    // Initialize components
    let metrics = Arc::new(Metrics::new());
    let cache = Arc::new(CacheManager::new(redis_pool.clone(), metrics.clone()));

    let state = AppState {
        cache,
        metrics,
        config: config.clone(),
    };

    // Build router
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/metrics", get(metrics_handler))
        .route("/cache/:key", get(get_cache))
        .route("/cache/:key", put(set_cache))
        .route("/cache/:key", delete(delete_cache))
        .route("/cache/batch", post(batch_operation))
        .route("/cache/invalidate/tag/:tag", delete(invalidate_by_tag))
        .route("/cache/stats", get(cache_stats))
        .route("/cache/warm", post(warm_cache))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = format!("{}:{}", config.host, config.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    
    info!("Cache service listening on {}", addr);
    
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check(State(state): State<AppState>) -> Result<Json<HealthResponse>> {
    let redis_connected = state.cache.ping().await.is_ok();
    
    Ok(Json(HealthResponse {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        redis_connected,
        uptime_seconds: 0, // Would track actual uptime in production
    }))
}

async fn get_cache(
    Path(key): Path<String>,
    Query(params): Query<CacheParams>,
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>> {
    let strategy = params.strategy
        .as_deref()
        .map(CacheStrategy::from_str)
        .unwrap_or(CacheStrategy::Standard);
    
    state.metrics.cache_request("get");
    
    match state.cache.get(&key, strategy).await {
        Ok(Some(value)) => {
            state.metrics.cache_hit();
            Ok(Json(value))
        }
        Ok(None) => {
            state.metrics.cache_miss();
            Err(AppError::NotFound(format!("Key '{}' not found", key)))
        }
        Err(e) => {
            error!("Cache get error: {}", e);
            Err(AppError::Internal(e.to_string()))
        }
    }
}

async fn set_cache(
    Path(key): Path<String>,
    Query(params): Query<CacheParams>,
    State(state): State<AppState>,
    Json(value): Json<serde_json::Value>,
) -> Result<StatusCode> {
    let ttl = params.ttl.unwrap_or(3600);
    let strategy = params.strategy
        .as_deref()
        .map(CacheStrategy::from_str)
        .unwrap_or(CacheStrategy::Standard);
    
    state.metrics.cache_request("set");
    
    state.cache.set(&key, value, ttl, strategy).await?;
    
    Ok(StatusCode::NO_CONTENT)
}

async fn delete_cache(
    Path(key): Path<String>,
    State(state): State<AppState>,
) -> Result<StatusCode> {
    state.metrics.cache_request("delete");
    state.cache.delete(&key).await?;
    Ok(StatusCode::NO_CONTENT)
}

async fn batch_operation(
    State(state): State<AppState>,
    Json(request): Json<BatchCacheRequest>,
) -> Result<Json<HashMap<String, bool>>> {
    let mut results = HashMap::new();
    
    for entry in request.entries {
        let success = if let Some(value) = entry.value.as_object() {
            let ttl = entry.ttl.unwrap_or(3600);
            state.cache.set(
                &entry.key,
                serde_json::Value::Object(value.clone()),
                ttl,
                CacheStrategy::Standard,
            ).await.is_ok()
        } else {
            false
        };
        
        results.insert(entry.key, success);
    }
    
    Ok(Json(results))
}

async fn invalidate_by_tag(
    Path(tag): Path<String>,
    State(state): State<AppState>,
) -> Result<StatusCode> {
    state.metrics.cache_request("invalidate_tag");
    state.cache.invalidate_by_tag(&tag).await?;
    Ok(StatusCode::NO_CONTENT)
}

async fn cache_stats(State(state): State<AppState>) -> Result<Json<serde_json::Value>> {
    let stats = state.cache.get_stats().await?;
    Ok(Json(stats))
}

async fn warm_cache(
    State(state): State<AppState>,
    Json(keys): Json<Vec<String>>,
) -> Result<Json<HashMap<String, bool>>> {
    let mut results = HashMap::new();
    
    for key in keys {
        // In production, would fetch from primary data source
        let warmed = state.cache.warm_cache(&key).await.is_ok();
        results.insert(key, warmed);
    }
    
    Ok(Json(results))
}

async fn metrics_handler(State(_state): State<AppState>) -> Result<String> {
    let encoder = TextEncoder::new();
    let metric_families = prometheus::gather();
    let mut buffer = vec![];
    encoder.encode(&metric_families, &mut buffer)
        .map_err(|e| AppError::Internal(e.to_string()))?;
    
    String::from_utf8(buffer)
        .map_err(|e| AppError::Internal(e.to_string()))
}