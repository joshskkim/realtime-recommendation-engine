use cache_service::store::{CacheStore, RecommendationCache};

#[tokio::test]
async fn test_store_get_set() {
    // connect
    let store = CacheStore::new("redis://127.0.0.1/")
        .expect("Redis should connect");

    let cache = RecommendationCache {
        user_id: "test_user".into(),
        items: vec!["item1".into(), "item2".into()],
    };

    // Write
    store.set(&cache).await.expect("Should insert");

    // Read
    let fetched = store.get("test_user").await.expect("Should fetch");
    assert!(fetched.is_some());
    let fetched = fetched.unwrap();
    assert_eq!(fetched.items, cache.items);
}
