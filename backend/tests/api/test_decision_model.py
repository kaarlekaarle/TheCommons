"""Tests for the two-level decision model."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.poll import Poll, DecisionType
from backend.config import settings

client = TestClient(app)


@pytest.mark.asyncio
async def test_poll_create_level_a_requires_choice(client: AsyncClient, auth_headers: dict):
    """Test that Level A polls require direction_choice."""
    poll_data = {
        "title": "Test Level A Poll",
        "description": "Test description",
        "decision_type": "level_a",
        "direction_choice": "Environmental Policy"
    }
    
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 200
    
    poll = response.json()
    assert poll["decision_type"] == "level_a"
    assert poll["direction_choice"] == "Environmental Policy"


@pytest.mark.asyncio
async def test_poll_create_level_a_missing_choice_fails(client: AsyncClient, auth_headers: dict):
    """Test that Level A polls without direction_choice fail."""
    poll_data = {
        "title": "Test Level A Poll",
        "description": "Test description",
        "decision_type": "level_a"
        # Missing direction_choice
    }
    
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_poll_create_level_b_ignores_direction_choice(client: AsyncClient, auth_headers: dict):
    """Test that Level B polls ignore direction_choice."""
    poll_data = {
        "title": "Test Level B Poll",
        "description": "Test description",
        "decision_type": "level_b",
        "direction_choice": "Some direction"  # Should be ignored
    }
    
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 200
    
    poll = response.json()
    assert poll["decision_type"] == "level_b"
    assert poll["direction_choice"] is None


@pytest.mark.asyncio
async def test_poll_read_includes_new_fields(client: AsyncClient, auth_headers: dict):
    """Test that poll read includes decision_type and direction_choice."""
    # Create a poll first
    poll_data = {
        "title": "Test Poll",
        "description": "Test description",
        "decision_type": "level_a",
        "direction_choice": "Environmental Policy"
    }
    
    create_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert create_response.status_code == 200
    
    poll_id = create_response.json()["id"]
    
    # Read the poll
    read_response = await client.get(f"/api/polls/{poll_id}", headers=auth_headers)
    assert read_response.status_code == 200
    
    poll = read_response.json()
    assert "decision_type" in poll
    assert "direction_choice" in poll
    assert poll["decision_type"] == "level_a"
    assert poll["direction_choice"] == "Environmental Policy"


@pytest.mark.asyncio
async def test_level_a_blocked_when_feature_disabled(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Test that Level A is blocked when feature flag is disabled."""
    # Disable Level A feature
    monkeypatch.setattr(settings, "LEVEL_A_ENABLED", False)
    
    poll_data = {
        "title": "Test Level A Poll",
        "description": "Test description",
        "decision_type": "level_a",
        "direction_choice": "Environmental Policy"
    }
    
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 403
    assert "Level A decisions are currently disabled" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_level_b_works_when_feature_disabled(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Test that Level B still works when Level A feature is disabled."""
    # Disable Level A feature
    monkeypatch.setattr(settings, "LEVEL_A_ENABLED", False)
    
    poll_data = {
        "title": "Test Level B Poll",
        "description": "Test description",
        "decision_type": "level_b"
    }
    
    response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    assert response.status_code == 200
    
    poll = response.json()
    assert poll["decision_type"] == "level_b"
    assert poll["direction_choice"] is None


@pytest.mark.asyncio
async def test_poll_list_includes_new_fields(client: AsyncClient, auth_headers: dict):
    """Test that poll list includes decision_type and direction_choice."""
    # Create a poll first
    poll_data = {
        "title": "Test Poll",
        "description": "Test description",
        "decision_type": "level_a",
        "direction_choice": "Environmental Policy"
    }
    
    await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    
    # Get poll list
    response = await client.get("/api/polls/", headers=auth_headers)
    assert response.status_code == 200
    
    polls = response.json()
    assert len(polls) > 0
    
    # Check that at least one poll has the new fields
    poll_with_fields = next((p for p in polls if "decision_type" in p), None)
    assert poll_with_fields is not None
    assert "decision_type" in poll_with_fields
    assert "direction_choice" in poll_with_fields
