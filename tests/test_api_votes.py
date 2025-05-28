import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient

pytestmark = pytest.mark.asyncio


async def test_create_vote(client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]) -> None:
    """Test creating a new vote."""
    # test_vote fixture already creates a poll, option, and vote
    vote_data = {"poll_id": test_vote["poll_id"], "option_id": test_vote["option_id"]}
    response = await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["poll_id"] == vote_data["poll_id"]
    assert data["option_id"] == vote_data["option_id"]
    assert "user_id" in data


async def test_get_poll_votes(client: TestClient, auth_headers: Dict[str, str], test_vote: Dict[str, Any]) -> None:
    """Test getting all votes for a poll."""
    poll_id = test_vote["poll_id"]
    # Create additional votes
    for _ in range(2):
        vote_data = {"poll_id": poll_id, "option_id": test_vote["option_id"]}
        await client.post("/api/votes/", json=vote_data, headers=auth_headers)
    response = await client.get(f"/api/votes/poll/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    votes = response.json()
    assert len(votes) >= 1
    for vote_data in votes:
        assert vote_data["poll_id"] == poll_id
        assert vote_data["option_id"] == test_vote["option_id"]
        assert "user_id" in vote_data


async def test_get_poll_votes_empty(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting votes for a poll with no votes."""
    # Create a poll
    poll_data = {"title": "Empty Poll", "description": "No votes yet"}
    poll_resp = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_resp.json()["id"]
    response = await client.get(f"/api/votes/poll/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


async def test_get_poll_votes_invalid_poll(client: TestClient, auth_headers: Dict[str, str]) -> None:
    """Test getting votes for a non-existent poll."""
    response = await client.get("/api/votes/poll/99999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Poll not found"}
