import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient

pytestmark = pytest.mark.asyncio


async def test_create_poll(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test creating a new poll."""
    poll_data = {"title": "Test Poll", "description": "This is a test poll"}
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == poll_data["title"]
    assert data["description"] == poll_data["description"]


async def test_get_polls(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting all polls."""
    response = await client.get("/api/polls/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_create_option(
    client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]
) -> None:
    """Test creating a new option."""
    option_data = {"text": "New Option", "poll_id": test_vote["poll_id"]}
    response = await client.post(
        "/api/options/", json=option_data, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == option_data["text"]
    assert data["poll_id"] == option_data["poll_id"]


async def test_get_options(
    client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]
) -> None:
    """Test getting options for a poll."""
    response = await client.get(
        f"/api/polls/{test_vote['poll_id']}/options/", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_create_vote(
    client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]
) -> None:
    """Test creating a new vote."""
    vote_data = {"poll_id": test_vote["poll_id"], "option_id": test_vote["option_id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["poll_id"] == vote_data["poll_id"]
    assert data["option_id"] == vote_data["option_id"]


async def test_get_votes(
    client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]
) -> None:
    """Test getting votes for a poll."""
    response = await client.get(
        f"/api/polls/{test_vote['poll_id']}/votes/", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
