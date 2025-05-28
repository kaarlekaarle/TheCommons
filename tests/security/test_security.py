"""Security tests for the API."""

import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.core.auth import create_access_token
from backend.config import settings
from tests.utils import create_test_user

pytestmark = pytest.mark.asyncio

async def test_invalid_token(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test API behavior with invalid tokens."""
    # Test with malformed token
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 401

    # Test with expired token
    expired_token = create_access_token(
        {"sub": "test@example.com"},
        expires_delta=timedelta(microseconds=1)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 401

    # Test with missing token
    response = await client.get("/api/users/me")
    assert response.status_code == 401

async def test_rate_limiting(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test rate limiting functionality."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Make multiple requests in quick succession
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = await client.get("/api/users/me", headers=headers)
        if response.status_code == 429:
            break
    else:
        pytest.fail("Rate limiting did not trigger")

async def test_sql_injection_prevention(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test SQL injection prevention."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt SQL injection in email
    injection_attempts = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; SELECT * FROM users; --"
    ]

    for attempt in injection_attempts:
        response = await client.post(
            "/api/users/",
            json={
                "email": attempt,
                "password": "password123",
                "full_name": "Test User"
            }
        )
        assert response.status_code in (400, 422)

async def test_xss_prevention(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test XSS prevention."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt XSS in poll title
    xss_attempts = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]

    for attempt in xss_attempts:
        response = await client.post(
            "/api/polls/",
            json={
                "title": attempt,
                "description": "Test Description",
                "end_date": "2024-12-31T23:59:59Z",
                "options": ["Option 1", "Option 2"]
            },
            headers=headers
        )
        assert response.status_code in (400, 422)

async def test_csrf_protection(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test CSRF protection."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://malicious-site.com"
    }

    # Attempt to create a poll from a different origin
    response = await client.post(
        "/api/polls/",
        json={
            "title": "Test Poll",
            "description": "Test Description",
            "end_date": "2024-12-31T23:59:59Z",
            "options": ["Option 1", "Option 2"]
        },
        headers=headers
    )
    assert response.status_code in (400, 403)

async def test_password_security(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test password security requirements."""
    # Test weak password
    weak_passwords = [
        "password",
        "123456",
        "qwerty",
        "abc123"
    ]

    for password in weak_passwords:
        response = await client.post(
            "/api/users/",
            json={
                "email": "test@example.com",
                "password": password,
                "full_name": "Test User"
            }
        )
        assert response.status_code in (400, 422)

async def test_session_security(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test session security."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Test secure headers
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers 