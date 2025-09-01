use warp::{Rejection, Reply};
use serde_json::json;
use crate::store::{CacheStore, RecommendationCache};

pub async fn get_cache(user_id: String) -> Result<impl Reply, Rejection> {
    let store = CacheStore::new("redis://127.0.0.1/").map_err(|_| warp::reject())?;
    match store.get(&user_id).await {
        Ok(Some(cache)) => Ok(warp::reply::json(&cache)),
        Ok(None)        => Ok(warp::reply::json(&json!({"error": "not found"}))),
        Err(_)          => Err(warp::reject()),
    }
}

pub async fn update_cache(
    user_id: String,
    mut cache: RecommendationCache,
) -> Result<impl Reply, Rejection> {
    // override whatever was in the JSON body
    cache.user_id = user_id.clone();

    let store = CacheStore::new("redis://127.0.0.1/").map_err(|_| warp::reject())?;
    store.set(&cache).await.map_err(|_| warp::reject())?;
    Ok(warp::reply::with_status("ok", warp::http::StatusCode::OK))
}
