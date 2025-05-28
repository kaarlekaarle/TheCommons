import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient

pytestmark = pytest.mark.asyncio


async def test_create_user(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test creating a new user."""
    user_data = {
        "email": "testuser1@example.com",
        "username": "test_user1",
        "password": "test_password1",
    }
    response = await client.post("/api/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data


async def test_create_user_duplicate_email(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test creating a user with a duplicate email."""
    user_data = {
        "email": "testuser2@example.com",
        "username": "test_user2",
        "password": "test_password2",
    }
    # Create user first
    await client.post("/api/users/", json=user_data)
    # Try to create another user with the same email
    user_data_dup = {
        "email": "testuser2@example.com",
        "username": "different_user",
        "password": "test_password2",
    }
    response = await client.post("/api/users/", json=user_data_dup)
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


async def test_get_user(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting a specific user."""
    user_data = {
        "email": "testuser3@example.com",
        "username": "test_user3",
        "password": "test_password3",
    }
    # Create user
    create_resp = await client.post("/api/users/", json=user_data)
    user_id = create_resp.json()["id"]
    # Get user
    response = await client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "hashed_password" not in data


async def test_get_user_not_found(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting a non-existent user."""
    response = await client.get("/api/users/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


async def test_get_users(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting all users."""
    # Create some users
    for i in range(3):
        user_data = {
            "email": f"testuserlist{i}@example.com",
            "username": f"test_user_list_{i}",
            "password": "test_password",
        }
        await client.post("/api/users/", json=user_data)
    # Get all users
    response = await client.get("/api/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3
    for user_data in users:
        assert "email" in user_data
        assert "username" in user_data
        assert "hashed_password" not in user_data
