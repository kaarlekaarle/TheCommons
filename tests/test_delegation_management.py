import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta

pytestmark = pytest.mark.asyncio

async def test_create_delegation(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test creating a new delegation."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create delegation
    delegation_data = {
        "delegatee_id": str(auth_headers2["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    response = await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["delegatee_id"] == delegation_data["delegatee_id"]
    assert data["poll_id"] == delegation_data["poll_id"]
    assert "id" in data

async def test_create_delegation_without_auth(client: AsyncClient):
    """Test creating a delegation without authentication."""
    delegation_data = {
        "delegatee_id": str(uuid4()),
        "poll_id": None,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    response = await client.post("/api/delegations/", json=delegation_data)
    assert response.status_code == 401

async def test_create_delegation_validation(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test delegation creation validation."""
    # Test self-delegation
    delegation_data = {
        "delegatee_id": str(auth_headers["user_id"]),  # Same as delegator
        "poll_id": None
    }
    response = await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)
    assert response.status_code == 400

    # Test invalid dates
    delegation_data = {
        "delegatee_id": str(auth_headers2["user_id"]),
        "poll_id": None,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat()  # End date before start date
    }
    response = await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)
    assert response.status_code == 400

async def test_delegation_limit_exceeded(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test delegation limit exceeded."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create 6 delegations (limit is 5)
    for i in range(6):
        delegation_data = {
            "delegatee_id": str(auth_headers2["user_id"]),
            "poll_id": str(poll_id),
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        response = await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)
        if i < 5:
            assert response.status_code == 201
        else:
            assert response.status_code == 400  # Should fail on 6th delegation

async def test_circular_delegation(client: AsyncClient, auth_headers: dict, auth_headers2: dict, auth_headers3: dict):
    """Test circular delegation detection."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create delegation chain: user1 -> user2 -> user3 -> user1 (circular)
    delegation1_data = {
        "delegatee_id": str(auth_headers2["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    await client.post("/api/delegations/", json=delegation1_data, headers=auth_headers)

    delegation2_data = {
        "delegatee_id": str(auth_headers3["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    await client.post("/api/delegations/", json=delegation2_data, headers=auth_headers2)

    # Try to create circular delegation
    delegation3_data = {
        "delegatee_id": str(auth_headers["user_id"]),  # Back to user1
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    response = await client.post("/api/delegations/", json=delegation3_data, headers=auth_headers3)
    assert response.status_code == 400

async def test_list_delegations(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test listing delegations."""
    # Create multiple delegations
    for i in range(3):
        delegation_data = {
            "delegatee_id": str(auth_headers2["user_id"]),
            "poll_id": None,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)

    # List delegations
    response = await client.get("/api/delegations/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["delegations"], list)
    assert len(data["delegations"]) >= 3

    # Verify delegation structure
    for delegation in data["delegations"]:
        assert "id" in delegation
        assert "delegatee_id" in delegation
        assert "poll_id" in delegation
        assert "start_date" in delegation
        assert "end_date" in delegation
        assert "created_at" in delegation

async def test_get_delegation_transparency(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test getting delegation transparency information."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create delegation
    delegation_data = {
        "delegatee_id": str(auth_headers2["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)

    # Get transparency info
    response = await client.get(f"/api/delegations/transparency/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "delegation_chain" in data
    assert "final_delegatee" in data
    assert len(data["delegation_chain"]) == 2  # Should include delegator and delegatee
    assert data["final_delegatee"]["id"] == str(auth_headers2["user_id"])

async def test_get_delegation_stats(client: AsyncClient, auth_headers: dict, auth_headers2: dict):
    """Test getting delegation statistics."""
    # Create some delegations first
    for i in range(3):
        delegation_data = {
            "delegatee_id": str(auth_headers2["user_id"]),
            "poll_id": None,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        await client.post("/api/delegations/", json=delegation_data, headers=auth_headers)

    # Get stats
    response = await client.get("/api/delegations/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_delegations" in data
    assert "active_delegations" in data
    assert "delegation_chains" in data

async def test_invalidate_stats_cache(client: AsyncClient, auth_headers: dict):
    """Test invalidating delegation statistics cache."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Invalidate cache for specific poll
    response = await client.post(f"/api/delegations/stats/invalidate?poll_id={poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Invalidate all cache
    response = await client.post("/api/delegations/stats/invalidate", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

async def test_delegation_chain_resolution(client: AsyncClient, auth_headers: dict, auth_headers2: dict, auth_headers3: dict):
    """Test delegation chain resolution."""
    # First create a poll
    poll_data = {
        "title": "Test Poll",
        "description": "Test description"
    }
    poll_response = await client.post("/api/polls/", json=poll_data, headers=auth_headers)
    poll_id = poll_response.json()["id"]

    # Create delegation chain: user1 -> user2 -> user3
    delegation1_data = {
        "delegatee_id": str(auth_headers2["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    await client.post("/api/delegations/", json=delegation1_data, headers=auth_headers)

    delegation2_data = {
        "delegatee_id": str(auth_headers3["user_id"]),
        "poll_id": str(poll_id),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    await client.post("/api/delegations/", json=delegation2_data, headers=auth_headers2)

    # Get delegation chain
    response = await client.get(f"/api/delegations/resolve/{poll_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["final_delegatee_id"] == str(auth_headers3["user_id"])
    assert len(data["chain"]) == 3  # Should include all users in the chain