"""Performance tests for the API."""

import pytest
import asyncio
import time
from typing import List, Dict
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.core.auth import create_access_token
from tests.utils import create_test_user, create_test_poll_with_options

pytestmark = pytest.mark.asyncio

async def measure_response_time(client: AsyncClient, method: str, url: str, **kwargs) -> float:
    """Measure the response time of an API call."""
    start_time = time.time()
    response = await getattr(client, method.lower())(url, **kwargs)
    end_time = time.time()
    assert response.status_code in (200, 201)
    return end_time - start_time

async def test_poll_creation_performance(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test the performance of poll creation."""
    # Create a test user
    user = await create_test_user(db_session)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Measure poll creation time
    poll_data = {
        "title": "Performance Test Poll",
        "description": "Test Description",
        "end_date": "2024-12-31T23:59:59Z",
        "options": ["Option 1", "Option 2", "Option 3"]
    }
    
    response_time = await measure_response_time(
        client, "post", "/api/polls/", json=poll_data, headers=headers
    )
    assert response_time < 1.0  # Should complete within 1 second

async def test_concurrent_voting_performance(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test the performance of concurrent voting."""
    # Create test users and poll
    users = [await create_test_user(db_session, email=f"user{i}@example.com") for i in range(10)]
    poll, options = await create_test_poll_with_options(db_session, users[0])
    
    # Create tokens for all users
    tokens = [create_access_token({"sub": user.email}) for user in users]
    headers_list = [{"Authorization": f"Bearer {token}"} for token in tokens]

    # Simulate concurrent voting
    async def vote(user_index: int):
        vote_data = {
            "poll_id": str(poll.id),
            "option_id": str(options[0].id)
        }
        return await client.post(
            "/api/votes/",
            json=vote_data,
            headers=headers_list[user_index]
        )

    # Measure time for concurrent votes
    start_time = time.time()
    tasks = [vote(i) for i in range(len(users))]
    responses = await asyncio.gather(*tasks)
    end_time = time.time()

    # Verify all votes were successful
    assert all(r.status_code == 201 for r in responses)
    total_time = end_time - start_time
    assert total_time < 5.0  # Should complete within 5 seconds

async def test_poll_results_performance(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test the performance of retrieving poll results."""
    # Create test users and poll
    user = await create_test_user(db_session)
    poll, options = await create_test_poll_with_options(db_session, user)
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple votes
    for option in options:
        vote_data = {
            "poll_id": str(poll.id),
            "option_id": str(option.id)
        }
        await client.post("/api/votes/", json=vote_data, headers=headers)

    # Measure time to get results
    response_time = await measure_response_time(
        client, "get", f"/api/polls/{poll.id}/results", headers=headers
    )
    assert response_time < 0.5  # Should complete within 500ms

async def test_delegation_performance(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test the performance of delegation operations."""
    # Create test users
    users = [await create_test_user(db_session, email=f"user{i}@example.com") for i in range(5)]
    poll, _ = await create_test_poll_with_options(db_session, users[0])
    
    # Create tokens
    tokens = [create_access_token({"sub": user.email}) for user in users]
    headers_list = [{"Authorization": f"Bearer {token}"} for token in tokens]

    # Measure delegation creation time
    async def create_delegation(user_index: int):
        delegation_data = {
            "delegate_id": str(users[0].id),
            "poll_id": str(poll.id)
        }
        return await client.post(
            "/api/delegations/",
            json=delegation_data,
            headers=headers_list[user_index]
        )

    # Test concurrent delegations
    start_time = time.time()
    tasks = [create_delegation(i) for i in range(1, len(users))]
    responses = await asyncio.gather(*tasks)
    end_time = time.time()

    # Verify all delegations were successful
    assert all(r.status_code == 201 for r in responses)
    total_time = end_time - start_time
    assert total_time < 3.0  # Should complete within 3 seconds

async def test_database_query_performance(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test the performance of database queries."""
    # Create test data
    users = [await create_test_user(db_session, email=f"user{i}@example.com") for i in range(20)]
    polls = []
    for user in users[:5]:
        poll, _ = await create_test_poll_with_options(db_session, user)
        polls.append(poll)

    # Measure time to query all polls
    start_time = time.time()
    token = create_access_token({"sub": users[0].email})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/polls/", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    query_time = end_time - start_time
    assert query_time < 0.5  # Should complete within 500ms 