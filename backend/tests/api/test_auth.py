import pytest
import redis
from fastapi import status

from backend.core.auth import verify_password, get_password_hash
from backend.models.user import User




def test_login_success(client, test_user):
    response = client.post(
        "/api/token",
        data={"username": "test@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"




def test_login_invalid_credentials(client):
    response = client.post(
        "/api/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




def test_register_success(client):
    response = client.post(
        "/api/users/",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data




def test_register_existing_email(client, test_user):
    response = client.post(
        "/api/users/",
        json={
            "email": "test@example.com",
            "username": "different_user",
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST




def test_get_current_user(client, test_token):
    response = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"




def test_get_current_user_unauthorized(client):
    response = client.get("/api/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




def test_register_invalid_password(client):
    """Test registration with invalid password format."""
    response = client.post(
        "/api/users/",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "weak",  # Missing uppercase, number, and special char
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data




def test_register_invalid_username(client):
    """Test registration with invalid username format."""
    response = client.post(
        "/api/users/",
        json={
            "email": "newuser@example.com",
            "username": "invalid user",  # Contains space
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data




def test_register_invalid_email(client):
    """Test registration with invalid email format."""
    response = client.post(
        "/api/users/",
        json={
            "email": "invalid-email",
            "username": "newuser",
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data




def test_register_existing_username(client, test_user):
    """Test registration with existing username."""
    response = client.post(
        "/api/users/",
        json={
            "email": "different@example.com",
            "username": "testuser",  # Same as test_user
            "password": "NewPassword123!",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_inactive_user(client, db_session):
    """Test login with inactive user."""
    # Create inactive user
    user = User(
        email="inactive@example.com",
        username="inactive",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = client.post(
        "/api/token",
        data={"username": "inactive@example.com", "password": "TestPassword123!"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




def test_token_validation(client, test_token):
    """Test token validation with valid token."""
    response = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == status.HTTP_200_OK




def test_token_validation_invalid(client):
    """Test token validation with invalid token."""
    response = client.get(
        "/api/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




def test_token_validation_malformed(client):
    """Test token validation with malformed authorization header."""
    response = client.get("/api/users/me", headers={"Authorization": "invalid_format"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# All configuration and executable code below this line has been removed.
