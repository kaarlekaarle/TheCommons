#!/usr/bin/env python3
"""
Show Application Status

Displays the current status of The Commons application and login credentials.
"""

import requests
import json

def check_backend():
    """Check if backend is running."""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            return True, "✅ Backend is running on http://localhost:8000"
        else:
            return False, f"❌ Backend responded with status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Backend is not running: {e}"

def check_frontend():
    """Check if frontend is running."""
    try:
        response = requests.get("http://localhost:5174", timeout=5)
        if response.status_code == 200:
            return True, "✅ Frontend is running on http://localhost:5174"
        else:
            return False, f"❌ Frontend responded with status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Frontend is not running: {e}"

def test_login():
    """Test login with a sample user."""
    try:
        response = requests.post(
            "http://localhost:8000/api/token",
            data={
                "username": "alice_community",
                "password": "password123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5
        )
        if response.status_code == 200:
            return True, "✅ Authentication is working"
        else:
            return False, f"❌ Authentication failed: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Authentication test failed: {e}"

def main():
    """Main function to show status."""
    print("🎯 The Commons Application Status")
    print("=" * 50)
    
    # Check backend
    backend_ok, backend_msg = check_backend()
    print(backend_msg)
    
    # Check frontend
    frontend_ok, frontend_msg = check_frontend()
    print(frontend_msg)
    
    # Test authentication
    auth_ok, auth_msg = test_login()
    print(auth_msg)
    
    print("\n📱 How to Access the Application:")
    print("1. Open your browser and go to: http://localhost:5174")
    print("2. You'll see the login/registration screen")
    print("3. Use any of these credentials to log in:")
    
    print("\n🔑 Available Login Credentials:")
    users = [
        "alice_community",
        "bob_organizer", 
        "carol_activist",
        "dave_thinker",
        "eve_leader",
        "frank_volunteer",
        "grace_advocate",
        "henry_planner",
        "iris_connector",
        "jack_builder"
    ]
    
    for user in users:
        print(f"   - Username: {user}")
        print(f"     Password: password123")
    
    print("\n📊 Available Content:")
    print("   - 10 users with different roles")
    print("   - 5 community proposals")
    print("   - 46 votes across all proposals")
    print("   - 18 delegations between users")
    print("   - 15 comments on proposals")
    
    print("\n🎯 What You Can Do:")
    print("   - Browse all proposals")
    print("   - View proposal details")
    print("   - Vote on proposals")
    print("   - Add comments")
    print("   - Set up delegations")
    print("   - View activity feed")
    
    if backend_ok and frontend_ok and auth_ok:
        print("\n✅ Everything is working! The application is ready to use.")
    else:
        print("\n⚠️  Some services may not be running properly.")
        print("   Make sure both backend and frontend are started.")

if __name__ == "__main__":
    main()
