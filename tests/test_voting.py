import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_vote(client: AsyncClient, auth_headers: dict):
    """Test creating a new vote."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    assert poll_response.status_code == 201
    poll = poll_response.json()

    # Then create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    assert option_response.status_code == 201
    option = option_response.json()

    # Finally create a vote
    vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["poll_id"] == poll["id"]
    assert data["option_id"] == option["id"]
    assert data["user_id"] is not None
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_vote_validation(client: AsyncClient, auth_headers: dict):
    """Test vote creation validation."""
    # Test without poll_id
    response = await client.post(
        "/api/votes/",
        json={"option_id": 1},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Test without option_id
    response = await client.post(
        "/api/votes/",
        json={"poll_id": 1},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Test without authentication
    response = await client.post(
        "/api/votes/",
        json={"poll_id": 1, "option_id": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote(client: AsyncClient, auth_headers: dict):
    """Test getting a vote."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Then create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Create a vote
    vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
    create_response = await client.post(
        "/api/votes/", json=vote_data, headers=auth_headers
    )
    vote = create_response.json()

    # Get the vote
    response = await client.get(f"/api/votes/{vote['id']}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == vote["id"]
    assert data["poll_id"] == poll["id"]
    assert data["option_id"] == option["id"]


@pytest.mark.asyncio
async def test_get_nonexistent_vote(client: AsyncClient, auth_headers: dict):
    """Test getting a nonexistent vote."""
    response = await client.get("/api/votes/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cast_vote(client: AsyncClient, auth_headers: dict):
    """Test casting a vote."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Then create two options
    option1_data = {"text": "Option 1", "poll_id": poll["id"]}
    option1_response = await client.post(
        "/api/options/", json=option1_data, headers=auth_headers
    )
    option1 = option1_response.json()

    option2_data = {"text": "Option 2", "poll_id": poll["id"]}
    option2_response = await client.post(
        "/api/options/", json=option2_data, headers=auth_headers
    )
    option2 = option2_response.json()

    # Cast a vote for option 1
    vote_data = {"poll_id": poll["id"], "option_id": option1["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    assert response.status_code == 201
    vote = response.json()

    # Update vote to option 2
    update_data = {"option_id": option2["id"]}
    response = await client.patch(
        f"/api/votes/{vote['id']}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    updated_vote = response.json()
    assert updated_vote["option_id"] == option2["id"]


@pytest.mark.asyncio
async def test_cast_vote_edge_cases(client: AsyncClient, auth_headers: dict):
    """Test edge cases for casting votes."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Cast a vote
    vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    vote = response.json()

    # Try to update with non-existent option
    update_data = {"option_id": 99999}
    response = await client.patch(
        f"/api/votes/{vote['id']}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 404

    # Try to update non-existent vote
    response = await client.patch(
        "/api/votes/99999", json=update_data, headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_vote(client: AsyncClient, auth_headers: dict):
    """Test updating a vote."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create two options
    option1_data = {"text": "Option 1", "poll_id": poll["id"]}
    option1_response = await client.post(
        "/api/options/", json=option1_data, headers=auth_headers
    )
    option1 = option1_response.json()

    option2_data = {"text": "Option 2", "poll_id": poll["id"]}
    option2_response = await client.post(
        "/api/options/", json=option2_data, headers=auth_headers
    )
    option2 = option2_response.json()

    # Create a vote
    vote_data = {"poll_id": poll["id"], "option_id": option1["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    vote = response.json()

    # Update the vote
    update_data = {"option_id": option2["id"]}
    response = await client.patch(
        f"/api/votes/{vote['id']}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["option_id"] == option2["id"]


@pytest.mark.asyncio
async def test_update_vote_edge_cases(client: AsyncClient, auth_headers: dict):
    """Test edge cases for updating votes."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Create a vote
    vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    vote = response.json()

    # Try to update with invalid option_id
    response = await client.patch(
        f"/api/votes/{vote['id']}",
        json={"option_id": 99999},
        headers=auth_headers,
    )
    assert response.status_code == 404

    # Try to update non-existent vote
    response = await client.patch(
        "/api/votes/99999",
        json={"option_id": option["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_vote(client: AsyncClient, auth_headers: dict):
    """Test deleting a vote."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Create a vote
    vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    vote = response.json()

    # Delete the vote
    response = await client.delete(f"/api/votes/{vote['id']}", headers=auth_headers)
    assert response.status_code == 200

    # Verify vote is deleted
    response = await client.get(f"/api/votes/{vote['id']}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_vote_edge_cases(client: AsyncClient, auth_headers: dict):
    """Test edge cases for deleting votes."""
    # Try to delete non-existent vote
    response = await client.delete("/api/votes/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_votes(client: AsyncClient, auth_headers: dict):
    """Test listing votes."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Create a few votes
    for _ in range(3):
        vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
        await client.post("/api/votes/", json=vote_data, headers=auth_headers)

    response = await client.get("/api/votes/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # There might be other votes from other tests


@pytest.mark.asyncio
async def test_list_votes_pagination(client: AsyncClient, auth_headers: dict):
    """Test vote listing pagination."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "This is a test poll",
    }
    poll_response = await client.post(
        "/api/polls/", json=poll_data, headers=auth_headers
    )
    poll = poll_response.json()

    # Create an option
    option_data = {"text": "Option 1", "poll_id": poll["id"]}
    option_response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    option = option_response.json()

    # Create multiple votes
    for _ in range(15):
        vote_data = {"poll_id": poll["id"], "option_id": option["id"]}
        await client.post("/api/votes/", json=vote_data, headers=auth_headers)

    # Test default pagination
    response = await client.get("/api/votes/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10  # Default limit

    # Test custom pagination
    response = await client.get("/api/votes/?offset=10&limit=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
