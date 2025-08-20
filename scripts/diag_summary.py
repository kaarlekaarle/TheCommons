#!/usr/bin/env python3
"""Diagnostic script for delegation summary endpoint.

Tests the /api/delegations/summary endpoint and reports:
- Response status and timing
- trace_id and error information
- Data structure and counts
- Authentication handling

Exits 0 for success, non-zero for errors.
"""
import sys
import time
import json
import requests
import argparse
from typing import Dict, Any


def test_endpoint(base_url: str, token: str = None) -> Dict[str, Any]:
    """Test the delegation summary endpoint."""
    url = f"{base_url}/api/delegations/summary"
    headers = {}
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    print(f"Testing: {url}")
    print(f"Headers: {headers}")
    
    start_time = time.time()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        duration_ms = (time.time() - start_time) * 1000
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {duration_ms:.2f}ms")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON response")
            return {
                "success": False,
                "error": "invalid_json",
                "status_code": response.status_code,
                "response_text": response.text[:200]
            }
        
        return {
            "success": True,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "data": data,
            "response_size": len(response.content)
        }
        
    except requests.exceptions.Timeout:
        print("ERROR: Request timeout")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed")
        return {"success": False, "error": "connection_error"}
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def analyze_response(result: Dict[str, Any]) -> bool:
    """Analyze the response and print detailed information."""
    if not result["success"]:
        print(f"❌ Request failed: {result.get('error', 'unknown')}")
        return False
    
    data = result["data"]
    status_code = result["status_code"]
    
    print(f"✅ Request successful ({status_code})")
    print(f"📊 Response size: {result['response_size']} bytes")
    print(f"⏱️  Duration: {result['duration_ms']:.2f}ms")
    
    # Analyze response structure
    if isinstance(data, dict):
        print("\n📋 Response structure:")
        
        # Check for 'ok' flag
        ok_flag = data.get("ok")
        print(f"   ok: {ok_flag}")
        
        # Check for meta information
        meta = data.get("meta", {})
        if meta:
            print(f"   meta.trace_id: {meta.get('trace_id', 'missing')}")
            print(f"   meta.generated_at: {meta.get('generated_at', 'missing')}")
            print(f"   meta.duration_ms: {meta.get('duration_ms', 'missing')}")
            
            errors = meta.get("errors", [])
            if errors:
                print(f"   meta.errors: {errors}")
            else:
                print("   meta.errors: none")
        
        # Check for counts
        counts = data.get("counts", {})
        if counts:
            print(f"   counts.mine: {counts.get('mine', 'missing')}")
            print(f"   counts.inbound: {counts.get('inbound', 'missing')}")
        
        # Check for delegation data
        global_delegate = data.get("global_delegate")
        per_label = data.get("per_label", [])
        
        print(f"   global_delegate: {bool(global_delegate)}")
        print(f"   per_label count: {len(per_label) if isinstance(per_label, list) else 'invalid'}")
        
        # Success criteria
        has_structure = all(key in data for key in ["ok", "counts", "meta"])
        has_trace_id = meta.get("trace_id") is not None
        has_reasonable_timing = result["duration_ms"] < 5000  # 5 seconds
        
        print(f"\n🔍 Validation:")
        print(f"   Has required structure: {has_structure}")
        print(f"   Has trace_id: {has_trace_id}")
        print(f"   Reasonable timing: {has_reasonable_timing}")
        
        if ok_flag is False and errors:
            print(f"   Expected errors for unauthenticated: {ok_flag is False}")
            
        return has_structure and has_trace_id and has_reasonable_timing
    
    else:
        print("❌ Response is not a JSON object")
        return False


def main():
    """Main diagnostic function."""
    parser = argparse.ArgumentParser(description="Test delegation summary endpoint")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                        help="Base URL for the API (default: http://localhost:8000)")
    parser.add_argument("--token", help="Authorization token for authenticated requests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🔬 Delegation Summary Endpoint Diagnostics")
    print("=" * 50)
    
    # Test unauthenticated request
    print("\n🔍 Testing unauthenticated request...")
    result_unauth = test_endpoint(args.base_url)
    success_unauth = analyze_response(result_unauth)
    
    # Test authenticated request if token provided
    success_auth = True
    if args.token:
        print("\n🔐 Testing authenticated request...")
        result_auth = test_endpoint(args.base_url, args.token)
        success_auth = analyze_response(result_auth)
    
    # Summary
    print("\n📝 Summary:")
    print(f"   Unauthenticated test: {'✅ PASS' if success_unauth else '❌ FAIL'}")
    if args.token:
        print(f"   Authenticated test: {'✅ PASS' if success_auth else '❌ FAIL'}")
    
    # Sample JSON for documentation
    if success_unauth and args.verbose:
        print("\n📄 Sample Response (unauthenticated):")
        print(json.dumps(result_unauth["data"], indent=2))
    
    # Exit code
    overall_success = success_unauth and success_auth
    if overall_success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
