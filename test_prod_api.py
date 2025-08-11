#!/usr/bin/env python3
"""
Simple test script to verify the production API is working.
This can be run from the host to test the production environment.
"""

import requests
import json
import time
from datetime import datetime

# Production API base URL
API_BASE_URL = "http://localhost:8001"

def test_health_endpoint():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_docs_endpoint():
    """Test the API documentation endpoint."""
    print("🔍 Testing API docs endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API docs endpoint working")
            return True
        else:
            print(f"❌ API docs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs endpoint error: {e}")
        return False

def test_poll_results_endpoint():
    """Test the poll results endpoint with a non-existent poll."""
    print("🔍 Testing poll results endpoint...")
    try:
        # Test with a non-existent poll ID
        fake_poll_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{API_BASE_URL}/api/polls/{fake_poll_id}/results", timeout=10)
        
        # Should return 404 or 401 (if authentication required)
        if response.status_code in [401, 404]:
            print("✅ Poll results endpoint responding correctly (authentication required or poll not found)")
            return True
        else:
            print(f"❌ Poll results endpoint unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Poll results endpoint error: {e}")
        return False

def test_authentication_endpoint():
    """Test the authentication endpoint."""
    print("🔍 Testing authentication endpoint...")
    try:
        # Test with invalid credentials
        data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = requests.post(f"{API_BASE_URL}/api/token", data=data, timeout=10)
        
        if response.status_code == 401:
            print("✅ Authentication endpoint working (correctly rejecting invalid credentials)")
            return True
        else:
            print(f"❌ Authentication endpoint unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication endpoint error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Production API")
    print("=" * 50)
    print(f"📅 Test started at: {datetime.now()}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print()
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("API Documentation", test_docs_endpoint),
        ("Authentication", test_authentication_endpoint),
        ("Poll Results", test_poll_results_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Production API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
