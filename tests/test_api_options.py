import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User

client = AsyncClient(app=app)


@pytest.mark.asyncio
async def test_create_option(client: AsyncClient, auth_headers, test_vote):
    """Test creating a new option."""
    option_data = {"text": "Test Option", "poll_id": test_vote["poll_id"]}
    response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == option_data["text"]
    assert data["poll_id"] == option_data["poll_id"]


@pytest.mark.asyncio
async def test_create_option_invalid_poll(client: AsyncClient, auth_headers):
    """Test creating an option for a non-existent poll."""
    option_data = {"text": "Test Option", "poll_id": "00000000-0000-0000-0000-000000000000"}
    response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Poll not found"


@pytest.mark.asyncio
async def test_get_option(client: AsyncClient, auth_headers, test_vote):
    """Test getting a specific option."""
    response = await client.get(f"/api/options/{test_vote['option_id']}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == test_vote["option"].text
    assert data["poll_id"] == test_vote["poll_id"]


@pytest.mark.asyncio
async def test_get_option_not_found(client: AsyncClient, auth_headers):
    """Test getting a non-existent option."""
    response = await client.get("/api/options/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Option not found"


@pytest.mark.asyncio
async def test_get_poll_options(client: AsyncClient, auth_headers, test_vote):
    """Test getting all options for a poll."""
    response = await client.get(f"/api/options/poll/{test_vote['poll_id']}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for option_data in data:
        assert "text" in option_data
        assert "poll_id" in option_data
        assert option_data["poll_id"] == test_vote["poll_id"]
