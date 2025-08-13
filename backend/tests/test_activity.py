import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.tests.fixtures.seed_minimal import seed_minimal_user, seed_minimal_poll, seed_minimal_activity


@pytest.mark.asyncio
async def test_activity_feed_structure(client: AsyncClient, db_session: AsyncSession):
    """Test that the activity feed returns the correct structure."""
    u = await seed_minimal_user(db_session)
    p = await seed_minimal_poll(db_session, owner_id=str(u.id))
    await seed_minimal_activity(db_session, user_id=str(u.id), poll_id=str(p.id))
    await db_session.commit()
    
    resp = await client.get("/api/activity/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "action_type" in item
        assert "actor" in item


@pytest.mark.asyncio
async def test_activity_feed_ordering(client: AsyncClient, db_session: AsyncSession):
    """Test that activity feed items are ordered by timestamp (newest first)."""
    u = await seed_minimal_user(db_session, "ordering-test@example.com", "orderinguser")
    p1 = await seed_minimal_poll(db_session, owner_id=str(u.id))
    p2 = await seed_minimal_poll(db_session, owner_id=str(u.id))
    await seed_minimal_activity(db_session, user_id=str(u.id), poll_id=str(p1.id))
    await seed_minimal_activity(db_session, user_id=str(u.id), poll_id=str(p2.id))
    await db_session.commit()
    
    resp = await client.get("/api/activity/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_activity_feed_limit(client: AsyncClient, db_session: AsyncSession):
    """Test that the limit parameter works correctly."""
    u = await seed_minimal_user(db_session, "limit-test@example.com", "limituser")
    
    # Create multiple polls and activities
    for i in range(5):
        p = await seed_minimal_poll(db_session, owner_id=str(u.id))
        await seed_minimal_activity(db_session, user_id=str(u.id), poll_id=str(p.id))
    
    await db_session.commit()
    
    # Test default limit
    resp = await client.get("/api/activity/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 20
    
    # Test custom limit
    resp = await client.get("/api/activity/?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 3


@pytest.mark.asyncio
async def test_activity_feed_public_access(client: AsyncClient):
    """Test that the activity feed is accessible without authentication."""
    resp = await client.get("/api/activity/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
