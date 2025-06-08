import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.core.auth import verify_password, get_password_hash
from backend.models.user import User

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    response = await async_client.post(
        "/api/token",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    response = await async_client.post(
        "/api/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "newpassword123",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"

@pytest.mark.asyncio
async def test_register_existing_email(async_client: AsyncClient, test_user: User):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": test_user.email,
            "username": "different",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_register_invalid_password(async_client: AsyncClient):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "short",  # Too short
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_invalid_username(async_client: AsyncClient):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": "test@example.com",
            "username": "test user",  # Contains space
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_invalid_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_register_existing_username(async_client: AsyncClient, test_user: User):
    response = await async_client.post(
        "/api/users/",
        json={
            "email": "different@example.com",
            "username": test_user.username,
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_login_inactive_user(async_client: AsyncClient, inactive_user: User):
    response = await async_client.post(
        "/api/token",
        data={"username": inactive_user.email, "password": "testpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_token_validation(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_token_validation_invalid(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalid_token"}
    response = await async_client.get("/api/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_token_validation_malformed(async_client: AsyncClient):
    headers = {"Authorization": "invalid_format"}
    response = await async_client.get("/api/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# All configuration and executable code below this line has been removed.
