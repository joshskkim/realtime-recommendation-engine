"""
Integration test for Phase 3 components
File: tests/phase3/test_phase3_integration.py
"""

import requests
import time
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"
CACHE_URL = "http://localhost:8082"


def test_ab_testing_flow():
    """Test complete A/B testing flow"""
    
    print("Testing A/B Testing Flow...")
    
    # 1. Create experiment
    experiment_data = {
        "name": "Integration Test Experiment",
        "description": "Testing recommendation strategies",
        "control_algorithm": "standard",
        "treatment_algorithms": [
            {"name": "variant_a", "algorithm": "enhanced_cf"},
            {"name": "variant_b", "algorithm": "hybrid_v2"}
        ],
        "allocation": {
            "control": 0.34,
            "variant_a": 0.33,
            "variant_b": 0.33
        },
        "metrics": ["conversion", "engagement", "revenue"],
        "target_sample_size": 1000
    }
    
    response = requests.post(f"{BASE_URL}/experiments/create", json=experiment_data)
    assert response.status_code == 200
    exp_id = response.json()["experiment_id"]
    print(f"✓ Created experiment: {exp_id}")
    
    # 2. Start experiment
    response = requests.post(f"{BASE_URL}/experiments/start/{exp_id}")
    assert response.status_code == 200
    print("✓ Started experiment")
    
    # 3. Get assignments for multiple users
    user_assignments = {}
    for i in range(100):
        user_id = f"test_user_{i}"
        response = requests.get(
            f"{BASE_URL}/experiments/assignment",
            params={"user_id": user_id, "experiment_id": exp_id}
        )
        assert response.status_code == 200
        variant = response.json()["variant"]
        user_assignments[user_id] = variant
    
    print(f"✓ Assigned 100 users to variants")
    
    # Check distribution
    variant_counts = {}
    for variant in user_assignments.values():
        variant_counts[variant] = variant_counts.get(variant, 0) + 1
    print(f"  Distribution: {variant_counts}")
    
    # 4. Track events
    for user_id, variant in list(user_assignments.items())[:20]:
        # Track engagement
        response = requests.post(f"{BASE_URL}/experiments/track", json={
            "user_id": user_id,
            "experiment_id": exp_id,
            "event_type": "engagement",
            "value": 3.5
        })
        assert response.status_code == 200
        
        # Track conversion for some users
        if user_id.endswith(('2', '5', '8')):
            response = requests.post(f"{BASE_URL}/experiments/track", json={
                "user_id": user_id,
                "experiment_id": exp_id,
                "event_type": "conversion",
                "value": 99.99
            })
            assert response.status_code == 200
    
    print("✓ Tracked user events")
    
    # 5. Get results
    response = requests.get(f"{BASE_URL}/experiments/results/{exp_id}")
    assert response.status_code == 200
    results = response.json()["results"]
    
    print("✓ Retrieved experiment results:")
    for group, metrics in results.items():
        print(f"  {group}: {metrics['conversion_rate']*100:.2f}% conversion")
    
    # 6. Get A/B tested recommendations
    response = requests.get(
        f"{BASE_URL}/experiments/recommendations/test_user_1",
        params={"limit": 5}
    )
    assert response.status_code == 200
    rec_data = response.json()
    print(f"✓ Got recommendations with strategy: {rec_data['strategy']}")
    
    # 7. Stop experiment
    response = requests.post(f"{BASE_URL}/experiments/stop/{exp_id}")
    assert response.status_code == 200
    print("✓ Stopped experiment")


def test_cold_start_handling():
    """Test cold start problem solutions"""
    
    print("\nTesting Cold Start Handling...")
    
    # 1. New user with demographics
    response = requests.post(f"{BASE_URL}/recommendations/cold-start", json={
        "user_id": "new_user_test_1",
        "demographics": {
            "age_group": "25-34",
            "gender": "female",
            "location": "US",
            "interests": ["technology", "fitness"]
        },
        "strategy": "hybrid",
        "limit": 10
    })
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    assert len(recs) > 0
    print(f"✓ Got {len(recs)} cold start recommendations for new user")
    
    # 2. New user without demographics (popularity-based)
    response = requests.post(f"{BASE_URL}/recommendations/cold-start", json={
        "user_id": "new_user_test_2",
        "strategy": "popularity",
        "limit": 5
    })
    assert response.status_code == 200
    print("✓ Got popularity-based recommendations")
    
    # 3. New item recommendations
    response = requests.post(f"{BASE_URL}/recommendations/cold-start/item", json={
        "item_id": "new_item_test_1",
        "item_features": {
            "category": "electronics",
            "price": 299.99,
            "brand": "TechCorp"
        },
        "limit": 10
    })
    assert response.status_code == 200
    users = response.json()["target_users"]
    print(f"✓ Got {len(users)} target users for new item")


def test_cache_service():
    """Test Rust cache service"""
    
    print("\nTesting Cache Service...")
    
    # 1. Health check
    response = requests.get(f"{CACHE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Cache service is healthy")
    
    # 2. Set cache value
    test_data = {
        "user_preferences": ["item1", "item2", "item3"],
        "score": 0.95
    }
    response = requests.put(
        f"{CACHE_URL}/cache/test_key_integration?ttl=300",
        json=test_data
    )
    assert response.status_code == 204
    print("✓ Set cache value")
    
    # 3. Get cache value
    response = requests.get(f"{CACHE_URL}/cache/test_key_integration")
    assert response.status_code == 200
    assert response.json() == test_data
    print("✓ Retrieved cache value")
    
    # 4. Batch operations
    batch_data = {
        "entries": [
            {
                "key": "batch_1",
                "value": {"data": "test1"},
                "ttl": 60
            },
            {
                "key": "batch_2",
                "value": {"data": "test2"},
                "ttl": 60
            }
        ]
    }
    response = requests.post(f"{CACHE_URL}/cache/batch", json=batch_data)
    assert response.status_code == 200
    results = response.json()
    assert results["batch_1"] == True
    assert results["batch_2"] == True
    print("✓ Batch operations completed")
    
    # 5. Get cache statistics
    response = requests.get(f"{CACHE_URL}/cache/stats")
    assert response.status_code == 200
    stats = response.json()
    print(f"✓ Cache stats: {stats.get('total_keys', 0)} keys")
    
    # 6. Delete cache value
    response = requests.delete(f"{CACHE_URL}/cache/test_key_integration")
    assert response.status_code == 204
    print("✓ Deleted cache value")


def test_stream_processor_integration():
    """Test Kafka Streams processor integration"""
    
    print("\nTesting Stream Processor...")
    
    # Send interaction event through API
    interaction = {
        "user_id": "stream_test_user",
        "item_id": "stream_test_item",
        "interaction_type": "view",
        "rating": 4.5,
        "session_id": "test_session_123"
    }
    
    response = requests.post(f"{BASE_URL}/interactions", json=interaction)
    assert response.status_code in [200, 201]
    print("✓ Sent interaction to stream processor")
    
    # Wait for processing
    time.sleep(2)
    
    # Check if trending items were updated
    response = requests.get(f"{BASE_URL}/recommendations/trending")
    assert response.status_code == 200
    trending = response.json().get("items", [])
    print(f"✓ Got {len(trending)} trending items")
    
    # Check if user profile was updated
    response = requests.get(f"{BASE_URL}/users/stream_test_user/profile")
    if response.status_code == 200:
        profile = response.json()
        print(f"✓ User profile updated: {profile.get('interaction_count', 0)} interactions")


def test_monitoring():
    """Test monitoring endpoints"""
    
    print("\nTesting Monitoring...")
    
    # 1. Prometheus metrics from cache service
    response = requests.get(f"{CACHE_URL}/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    assert "cache_hits_total" in metrics_text
    assert "cache_misses_total" in metrics_text
    print("✓ Cache service metrics available")
    
    # 2. ML service metrics
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    print("✓ ML service metrics available")
    
    # 3. Check Prometheus
    try:
        response = requests.get("http://localhost:9090/-/healthy")
        if response.status_code == 200:
            print("✓ Prometheus is healthy")
    except:
        print("⚠ Prometheus not accessible")
    
    # 4. Check Grafana
    try:
        response = requests.get("http://localhost:3000/api/health")
        if response.status_code == 200:
            print("✓ Grafana is healthy")
    except:
        print("⚠ Grafana not accessible")


def run_all_tests():
    """Run all Phase 3 integration tests"""
    
    print("=" * 50)
    print("PHASE 3 INTEGRATION TESTS")
    print("=" * 50)
    
    try:
        test_cache_service()
        test_cold_start_handling()
        test_ab_testing_flow()
        test_stream_processor_integration()
        test_monitoring()
        
        print("\n" + "=" * 50)
        print("✅ ALL PHASE 3 TESTS PASSED!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    # Wait for services to be ready
    print("Waiting for services to initialize...")
    time.sleep(5)
    
    run_all_tests()