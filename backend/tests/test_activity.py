import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.tests.fixtures.seed_minimal import seed_minimal_activity, seed_minimal_user, seed_minimal_poll
from backend.models.user import User
from backend.models.poll import Poll, PollStatus, PollVisibility, DecisionType
from backend.core.security import get_password_hash


@pytest.mark.asyncio
async def test_activity_feed_structure(async_client: AsyncClient, db_session: AsyncSession):
    """Test that the activity feed returns the correct structure."""
    
    # Seed minimal activity data
    seeded_data = await seed_minimal_activity(db_session)
    
    # Test the activity feed
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # Should have at least proposal, vote, and delegation
    
    # Check structure of first item
    first_item = data[0]
    assert "type" in first_item
    assert "id" in first_item
    assert "user" in first_item
    assert "timestamp" in first_item
    assert "details" in first_item
    
    # Check user structure
    user = first_item["user"]
    assert "id" in user
    assert "username" in user
    
    # Check valid types
    valid_types = ["proposal", "vote", "delegation"]
    for item in data:
        assert item["type"] in valid_types


@pytest.mark.asyncio
async def test_activity_feed_ordering(async_client: AsyncClient, db_session: AsyncSession):
    """Test that activity feed items are ordered by timestamp (newest first)."""
    
    # Create test user
    user = await seed_minimal_user(db_session, "ordering-test@example.com", "orderinguser")
    
    # Create two proposals with different timestamps
    # Older proposal
    old_poll = Poll(
        title="Older Proposal",
        description="This should appear second",
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(hours=2),
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        allow_delegation=True,
        require_authentication=False,
        max_votes_per_user=1,
        decision_type=DecisionType.LEVEL_B,
        direction_choice="up_down",
    )
    
    # Newer proposal  
    new_poll = Poll(
        title="Newer Proposal",
        description="This should appear first",
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(hours=1),
        status=PollStatus.ACTIVE,
        visibility=PollVisibility.PUBLIC,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        allow_delegation=True,
        require_authentication=False,
        max_votes_per_user=1,
        decision_type=DecisionType.LEVEL_B,
        direction_choice="up_down",
    )
    
    db_session.add(old_poll)
    db_session.add(new_poll)
    await db_session.commit()
    await db_session.refresh(old_poll)
    await db_session.refresh(new_poll)
    
    # Test the activity feed
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    
    # Find our test proposals
    newer_found = False
    older_found = False
    
    for item in data:
        if item["type"] == "proposal" and "Newer Proposal" in item["details"]:
            newer_found = True
        elif item["type"] == "proposal" and "Older Proposal" in item["details"]:
            older_found = True
            
        # If we found the older one, we should have already found the newer one
        if older_found and not newer_found:
            pytest.fail("Older proposal appeared before newer proposal")
    
    assert newer_found, "Newer proposal not found in feed"
    assert older_found, "Older proposal not found in feed"


@pytest.mark.asyncio
async def test_activity_feed_limit(async_client: AsyncClient, db_session: AsyncSession):
    """Test that the limit parameter works correctly."""
    
    # Create test user
    user = await seed_minimal_user(db_session, "limit-test@example.com", "limituser")
    
    # Create multiple proposals
    for i in range(25):
        poll = Poll(
            title=f"Proposal {i}",
            description=f"Test proposal {i}",
            created_by=user.id,
            status=PollStatus.ACTIVE,
            visibility=PollVisibility.PUBLIC,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            allow_delegation=True,
            require_authentication=False,
            max_votes_per_user=1,
            decision_type=DecisionType.LEVEL_B,
            direction_choice="up_down",
        )
        db_session.add(poll)
    
    await db_session.commit()
    
    # Test default limit (20)
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 20
    
    # Test custom limit
    response = await async_client.get("/api/activity/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_activity_feed_public_access(async_client: AsyncClient):
    """Test that the activity feed is accessible without authentication."""
    
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
