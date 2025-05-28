import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

async def test_create_poll(client: AsyncClient, auth_headers: dict):
    """Test creating a new poll."""
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll description"
    }
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == poll_data["title"]
    assert data["description"] == poll_data["description"]
    assert "id" in data
    assert "created_by" in data
    assert "created_at" in data

async def test_create_poll_without_auth(client: AsyncClient):
    """Test creating a poll without authentication."""
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    response = await client.post("/api/polls/", json=poll_data)
    assert response.status_code == 401

async def test_create_poll_validation(client: AsyncClient, auth_headers: dict):
    """Test poll creation validation."""
    # Test empty title
    response = await client.post(
        "/api/polls/",
        json={"title": "", "description": "Test description"},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test title too long
    response = await client.post(
        "/api/polls/",
        json={"title": "a" * 201, "description": "Test description"},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test description too long
    response = await client.post(
        "/api/polls/",
        json={"title": "Test Poll", "description": "a" * 1001},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test missing required fields
    response = await client.post(
        "/api/polls/",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test missing title
    response = await client.post(
        "/api/polls/",
        json={"description": "Test description"},
        headers=auth_headers
    )
    assert response.status_code == 422

async def test_list_polls(client: AsyncClient, auth_headers: dict):
    """Test listing polls with pagination."""
    # Create multiple polls
    for i in range(3):
        poll_data = {
            "title": f"Test Poll {i}",
            "description": f"Test description {i}"
        }
        await client.post("/api/polls/", json=poll_data, headers=auth_headers)

    # Test default pagination
    response = await client.get("/api/polls/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Test pagination with limit
    response = await client.get("/api/polls/?limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Test pagination with skip
    response = await client.get("/api/polls/?skip=1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

async def test_get_poll(client: AsyncClient, auth_headers: dict):
    """Test getting a specific poll."""
    # Create a poll first
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = create_response.json()["id"]

    # Get the poll
    response = await client.get(f"/api/polls/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == poll_id
    assert data["title"] == poll_data["title"]
    assert data["description"] == poll_data["description"]

    # Test non-existent poll
    response = await client.get(f"/api/polls/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404

async def test_update_poll(client: AsyncClient, auth_headers: dict):
    """Test updating a poll."""
    # Create a poll first
    poll_data = {
        "title": "Original Title",
        "description": "Original description"
    }
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = create_response.json()["id"]

    # Update the poll
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = await client.put(f"/api/polls/{poll_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]

    # Test updating with invalid data
    invalid_data = {
        "title": "",  # Empty title
        "description": "Updated description"
    }
    response = await client.put(f"/api/polls/{poll_id}", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422

    # Test updating with too long title
    invalid_data = {
        "title": "a" * 201,  # Title too long
        "description": "Updated description"
    }
    response = await client.put(f"/api/polls/{poll_id}", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422

    # Test updating non-existent poll
    response = await client.put(f"/api/polls/{uuid4()}", json=update_data, headers=auth_headers)
    assert response.status_code == 404

async def test_partial_update_poll(client: AsyncClient, auth_headers: dict):
    """Test partially updating a poll."""
    # Create a poll first
    poll_data = {
        "title": "Original Title",
        "description": "Original description"
    }
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = create_response.json()["id"]

    # Partially update the poll
    update_data = {
        "title": "Updated Title"
    }
    response = await client.patch(f"/api/polls/{poll_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == poll_data["description"]  # Should remain unchanged

async def test_delete_poll(client: AsyncClient, auth_headers: dict):
    """Test deleting a poll."""
    # Create a poll first
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = create_response.json()["id"]

    # Delete the poll
    response = await client.delete(f"/api/polls/{poll_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify poll is deleted
    response = await client.get(f"/api/polls/{poll_id}", headers=auth_headers)
    assert response.status_code == 404

    # Test deleting non-existent poll
    response = await client.delete(f"/api/polls/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404

    # Test deleting already deleted poll
    response = await client.delete(f"/api/polls/{poll_id}", headers=auth_headers)
    assert response.status_code == 404

async def test_poll_ownership(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test poll ownership verification."""
    # Create a poll with first user
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = create_response.json()["id"]

    # Try to update with second user
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = await client.put(f"/api/polls/{poll_id}", json=update_data, headers=auth_headers2)
    assert response.status_code == 403

    # Try to delete with second user
    response = await client.delete(f"/api/polls/{poll_id}", headers=auth_headers2)
    assert response.status_code == 403