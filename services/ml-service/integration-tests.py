#!/usr/bin/env python3
"""
Simple integration tests
"""
import subprocess
import sys
import json

ML_SERVICE_URL = "http://localhost:8000"

def run_curl(url, method="GET", data=None):
    """Run curl command and return response"""
    cmd = ["curl", "-s"]
    
    if method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def test_health():
    """Test health endpoint"""
    success, response = run_curl(f"{ML_SERVICE_URL}/health")
    if success and "healthy" in response:
        print("✅ Health check passed")
        return True
    print("❌ Health check failed")
    return False

def test_recommendations():
    """Test recommendations endpoint"""
    success, response = run_curl(f"{ML_SERVICE_URL}/recommendations/user/1?limit=3")
    if success and "recommendations" in response:
        print("✅ Recommendations endpoint passed")
        return True
    print("❌ Recommendations endpoint failed")
    return False

def test_interactions():
    """Test interactions endpoint"""
    data = {"user_id": 1, "item_id": 2, "interaction_type": "view"}
    success, response = run_curl(f"{ML_SERVICE_URL}/interactions", "POST", data)
    if success and "recorded" in response:
        print("✅ Interactions endpoint passed")
        return True
    print("❌ Interactions endpoint failed")
    return False

def main():
    print("🧪 Running integration tests...")
    
    tests = [test_health, test_recommendations, test_interactions]
    passed = sum(1 for test in tests if test())
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()