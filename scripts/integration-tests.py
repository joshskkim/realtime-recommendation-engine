#!/usr/bin/env python3
"""
Integration tests for the recommendation engine
"""

import requests
import time
import sys
from typing import Dict, Any

# Configuration
ML_SERVICE_URL = "http://localhost:8000"
KAFKA_UI_URL = "http://localhost:8080"
REDIS_COMMANDER_URL = "http://localhost:8081"

def test_service_health(url: str, service_name: str) -> bool:
    """Test if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} connection failed: {e}")
        return False

def test_ml_service_endpoints():
    """Test ML service specific endpoints"""
    print("\n🧪 Testing ML Service endpoints...")
    
    # Test recommendation endpoint
    try:
        response = requests.get(f"{ML_SERVICE_URL}/recommendations/user/1?limit=5")
        if response.status_code == 200:
            data = response.json()
            if "recommendations" in data:
                print(f"✅ Recommendations endpoint working - got {len(data['recommendations'])} recommendations")
                return True
        print(f"❌ Recommendations endpoint failed: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Recommendations endpoint error: {e}")
        return False

def test_ui_access():
    """Test if UIs are accessible"""
    print("\n🖥️  Testing UI access...")
    
    uis = [
        (KAFKA_UI_URL, "Kafka UI"),
        (REDIS_COMMANDER_URL, "Redis Commander")
    ]
    
    results = []
    for url, name in uis:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} accessible")
                results.append(True)
            else:
                print(f"⚠️  {name} returned {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name} not accessible: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all integration tests"""
    print("🚀 Running integration tests for Recommendation Engine...")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: ML Service Health
    if test_service_health(ML_SERVICE_URL, "ML Service"):
        tests_passed += 1
    
    # Test 2: ML Service Endpoints
    if test_ml_service_endpoints():
        tests_passed += 1
    
    # Test 3: UI Access
    if test_ui_access():
        tests_passed += 1
    
    # Results
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()