import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.core.auth import verify_password, get_password_hash
from backend.models.user import User

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/users/",
        json={
            "email": "new@example.com",
            "username": "completely_new_user",
            "password": "newpassword123",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "completely_new_user"

@pytest.mark.asyncio
async def test_register_existing_email(client: AsyncClient):
    # First, create a user
    user_data = {
        "email": "existing@example.com",
        "username": "existinguser",
        "password": "password123",
    }
    response = await client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Then try to create another user with the same email
    response = await client.post(
        "/api/users/",
        json={
            "email": "existing@example.com",
            "username": "different",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get("/api/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_invalid_password(client: AsyncClient):
    response = await client.post(
        "/api/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "short",  # Too short
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_invalid_username(client: AsyncClient):
    response = await client.post(
        "/api/users/",
        json={
            "email": "test@example.com",
            "username": "test user",  # Contains space
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/users/",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_existing_username(client: AsyncClient):
    # First, create a user
    user_data = {
        "email": "user@example.com",
        "username": "existingusername",
        "password": "password123",
    }
    response = await client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Then try to create another user with the same username
    response = await client.post(
        "/api/users/",
        json={
            "email": "different@example.com",
            "username": "existingusername",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, inactive_user: User):
    response = await client.post(
        "/api/token",
        data={"username": inactive_user.email, "password": "testpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_token_validation(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_token_validation_invalid(client: AsyncClient):
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_token_validation_malformed(client: AsyncClient):
    headers = {"Authorization": "invalid_format"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# All configuration and executable code below this line has been removed.
