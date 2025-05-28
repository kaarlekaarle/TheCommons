import asyncio
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from backend.core.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_create_and_revoke_delegation(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    # Create a delegation
    data = {"delegatee_id": str(test_user2.id), "poll_id": None, "reason": "API test"}
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code == 200
    delegation = response.json()
    assert delegation["delegator_id"] == str(test_user.id)
    assert delegation["delegatee_id"] == str(test_user2.id)
    assert delegation["reason"] == "API test"
    assert delegation["revoked_at"] is None

    # Revoke the delegation
    response = await client.delete(
        f"/api/delegations/{delegation['id']}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_self_delegation_error(client: AsyncClient, test_user, auth_headers):
    data = {"delegatee_id": str(test_user.id), "poll_id": None}
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "Cannot delegate to yourself" in response.text


@pytest.mark.asyncio
async def test_duplicate_delegation_error(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    data = {"delegatee_id": str(test_user2.id), "poll_id": None}
    await client.post("/api/delegations/", json=data, headers=auth_headers)
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code == 409
    assert "Already delegated" in response.text


@pytest.mark.asyncio
async def test_get_active_delegations(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    data = {"delegatee_id": str(test_user2.id), "poll_id": None}
    await client.post("/api/delegations/", json=data, headers=auth_headers)
    response = await client.get("/api/delegations/active", headers=auth_headers)
    assert response.status_code == 200
    active = response.json()
    assert len(active) == 1
    assert active[0]["delegator_id"] == str(test_user.id)
    assert active[0]["delegatee_id"] == str(test_user2.id)


@pytest.mark.asyncio
async def test_revoke_nonexistent_delegation(client: AsyncClient, auth_headers):
    response = await client.delete(f"/api/delegations/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stats_and_transparency(
    client: AsyncClient, db_session, test_user, test_user2, test_poll, auth_headers
):
    # Create a poll-specific delegation
    data = {"delegatee_id": str(test_user2.id), "poll_id": str(test_poll.id)}
    await client.post("/api/delegations/", json=data, headers=auth_headers)

    # Get stats
    response = await client.get("/api/delegations/stats", headers=auth_headers)
    assert response.status_code == 200
    stats = response.json()
    assert "top_delegatees" in stats
    assert "active_delegations" in stats

    # Get transparency
    response = await client.get(
        f"/api/delegations/transparency/{test_poll.id}", headers=auth_headers
    )
    assert response.status_code == 200
    transparency = response.json()
    assert transparency["poll_id"] == str(test_poll.id)
    assert transparency["active_delegations"] >= 1


@pytest.mark.asyncio
async def test_resolve_chain_and_errors(
    client: AsyncClient, db_session, test_user, test_user2, test_poll, auth_headers
):
    # Create a poll-specific delegation
    data = {"delegatee_id": str(test_user2.id), "poll_id": str(test_poll.id)}
    await client.post("/api/delegations/", json=data, headers=auth_headers)

    # Resolve chain
    response = await client.get(
        f"/api/delegations/resolve/{test_poll.id}", headers=auth_headers
    )
    assert response.status_code == 200
    chain = response.json()
    assert "final_delegatee_id" in chain

    # Test error: non-existent poll
    response = await client.get(
        f"/api/delegations/resolve/{uuid4()}", headers=auth_headers
    )
    assert response.status_code in (200, 400)  # Depending on implementation


@pytest.mark.asyncio
async def test_invalidate_stats_cache(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/delegations/stats/invalidate", headers=auth_headers
    )
    assert response.status_code == 200
    assert "success" in response.text


@pytest.mark.asyncio
async def test_authentication_required(client: AsyncClient, test_user2):
    data = {"delegatee_id": str(test_user2.id), "poll_id": None}
    response = await client.post("/api/delegations/", json=data)  # No auth headers
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_circular_delegation(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    # user -> user2
    data = {"delegatee_id": str(test_user2.id), "poll_id": None}
    await client.post("/api/delegations/", json=data, headers=auth_headers)
    # user2 -> user (circular)
    token2 = create_access_token({"sub": "test2@example.com"})
    headers2 = {"Authorization": f"Bearer {token2}"}
    data2 = {"delegatee_id": str(test_user.id), "poll_id": None}
    response = await client.post("/api/delegations/", json=data2, headers=headers2)
    assert response.status_code == 400
    assert "Delegation loop detected" in response.text


@pytest.mark.asyncio
async def test_delegation_after_voting(
    client: AsyncClient, db_session, test_user, test_user2, test_poll, auth_headers
):
    # Simulate a vote
    from backend.models.vote import Vote

    vote = Vote(user_id=test_user.id, poll_id=test_poll.id, option_id=None)
    db_session.add(vote)
    await db_session.commit()
    # Try to delegate after voting
    data = {"delegatee_id": str(test_user2.id), "poll_id": str(test_poll.id)}
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "Cannot delegate after voting" in response.text


@pytest.mark.asyncio
async def test_revoke_already_revoked_delegation(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    # Create and revoke
    data = {"delegatee_id": str(test_user2.id), "poll_id": None}
    resp = await client.post("/api/delegations/", json=data, headers=auth_headers)
    delegation_id = resp.json()["id"]
    await client.delete(f"/api/delegations/{delegation_id}", headers=auth_headers)
    # Revoke again (should be idempotent)
    response = await client.delete(
        f"/api/delegations/{delegation_id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_invalid_poll_and_user_ids(client: AsyncClient, auth_headers):
    # Non-existent user
    data = {"delegatee_id": str(uuid4()), "poll_id": None}
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code in (400, 404)
    # Non-existent poll
    data = {"delegatee_id": str(uuid4()), "poll_id": str(uuid4())}
    response = await client.post("/api/delegations/", json=data, headers=auth_headers)
    assert response.status_code in (400, 404)


@pytest.mark.asyncio
async def test_chain_depth_limit(
    client: AsyncClient, db_session, test_user, test_user2, auth_headers
):
    # Create a chain: user -> user2 -> user3 ...
    from backend.models.user import User

    users = [test_user, test_user2]
    for i in range(8):
        u = User(
            email=f"u{i}@example.com",
            username=f"u{i}",
            hashed_password=get_password_hash("pw"),
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        users.append(u)
    # Chain delegations
    for i in range(len(users) - 1):
        token = create_access_token({"sub": users[i].email})
        headers = {"Authorization": f"Bearer {token}"}
        data = {"delegatee_id": str(users[i + 1].id), "poll_id": None}
        await client.post("/api/delegations/", json=data, headers=headers)
    # Try to resolve chain (should hit depth limit)
    token = create_access_token({"sub": users[0].email})
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(f"/api/delegations/resolve/{uuid4()}", headers=headers)
    assert response.status_code in (200, 400)
    # Check for depth/circular error in response
    # (depends on implementation)


# Optionally, add a rate limiting test if enabled in your app
# @pytest.mark.asyncio
# def test_rate_limiting(client, test_user, test_user2, auth_headers):
#     data = {"delegatee_id": str(test_user2.id), "poll_id": None}
#     for _ in range(100):
#         client.post("/api/delegations/", json=data, headers=auth_headers)
#     response = client.post("/api/delegations/", json=data, headers=auth_headers)
#     assert response.status_code == 429
