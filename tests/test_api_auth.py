import pytest
from httpx import AsyncClient
from typing import Dict, Any

@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user: Any) -> None:
    response = await client.post(
        "/api/token", data={"username": test_user.username, "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: Any) -> None:
    response = await client.post(
        "/api/token", data={"username": test_user.username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: Dict[str, str], test_user: Any) -> None:
    response = await client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    print("\nResponse status:", response.status_code)
    print("Response headers:", dict(response.headers))
    print("RESPONSE BODY:", response.text)
    print("Request headers:", response.request.headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
