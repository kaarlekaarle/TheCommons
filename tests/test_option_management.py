import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

async def test_create_option(client: AsyncClient, auth_headers: dict):
    """Test creating a new option."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create an option
    option_data = {
        "text": "Test Option",
        "poll_id": str(poll_id)  # Convert UUID to string
    }
    response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == option_data["text"]
    assert data["poll_id"] == poll_id
    assert "id" in data

async def test_create_option_without_auth(client: AsyncClient):
    """Test creating an option without authentication."""
    option_data = {
        "text": "Test Option",
        "poll_id": str(uuid4())
    }
    response = await client.post("/api/options/", json=option_data)
    assert response.status_code == 401

async def test_create_option_validation(client: AsyncClient, auth_headers: dict):
    """Test option creation validation."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Test empty text
    response = await client.post(
        "/api/options/",
        json={"text": "", "poll_id": str(poll_id)},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test text too long
    response = await client.post(
        "/api/options/",
        json={"text": "a" * 501, "poll_id": str(poll_id)},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test non-existent poll
    response = await client.post(
        "/api/options/",
        json={"text": "Test Option", "poll_id": str(uuid4())},
        headers=auth_headers
    )
    assert response.status_code == 404

    # Test missing poll_id
    response = await client.post(
        "/api/options/",
        json={"text": "Test Option"},
        headers=auth_headers
    )
    assert response.status_code == 422

async def test_get_poll_options(client: AsyncClient, auth_headers: dict):
    """Test getting options for a poll."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create multiple options
    for i in range(3):
        option_data = {
            "text": f"Option {i}",
            "poll_id": str(poll_id)
        }
        await client.post("/api/options/", json=option_data, headers=auth_headers)

    # Get options for the poll
    response = await client.get(f"/api/options/poll/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    for option in data:
        assert option["poll_id"] == poll_id
        assert "text" in option
        assert "id" in option

    # Test non-existent poll
    response = await client.get(f"/api/options/poll/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404

async def test_update_option(client: AsyncClient, auth_headers: dict):
    """Test updating an option."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create an option
    option_data = {
        "text": "Original Option",
        "poll_id": str(poll_id)
    }
    create_response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    option_id = create_response.json()["id"]

    # Update the option
    update_data = {
        "text": "Updated Option"
    }
    response = await client.put(f"/api/options/{option_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == update_data["text"]
    assert data["poll_id"] == poll_id

    # Test updating non-existent option
    response = await client.put(f"/api/options/{uuid4()}", json=update_data, headers=auth_headers)
    assert response.status_code == 404

async def test_partial_update_option(client: AsyncClient, auth_headers: dict):
    """Test partially updating an option."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create an option
    option_data = {
        "text": "Original Option",
        "poll_id": str(poll_id)
    }
    create_response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    option_id = create_response.json()["id"]

    # Partially update the option
    update_data = {
        "text": "Updated Option"
    }
    response = await client.patch(f"/api/options/{option_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == update_data["text"]
    assert data["poll_id"] == poll_id

async def test_delete_option(client: AsyncClient, auth_headers: dict):
    """Test deleting an option."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create an option
    option_data = {
        "text": "Test Option",
        "poll_id": str(poll_id)
    }
    create_response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    option_id = create_response.json()["id"]

    # Delete the option
    response = await client.delete(f"/api/options/{option_id}", headers=auth_headers)
    assert response.status_code == 204  # Changed from 200 to 204 for successful deletion

    # Verify option is deleted
    response = await client.get(f"/api/options/poll/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Test deleting non-existent option
    response = await client.delete(f"/api/options/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404

async def test_option_ownership(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test option ownership verification."""
    # First create a poll with first user
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create an option
    option_data = {
        "text": "Test Option",
        "poll_id": str(poll_id)
    }
    create_response = await client.post("/api/options/", json=option_data, headers=auth_headers)
    option_id = create_response.json()["id"]

    # Try to update with second user
    update_data = {
        "text": "Updated Option"
    }
    response = await client.put(f"/api/options/{option_id}", json=update_data, headers=auth_headers2)
    assert response.status_code == 403

    # Try to delete with second user
    response = await client.delete(f"/api/options/{option_id}", headers=auth_headers2)
    assert response.status_code == 403