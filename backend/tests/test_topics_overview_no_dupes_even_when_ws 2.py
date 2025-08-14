import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.poll import Poll
from backend.models.label import Label
from backend.models.poll_label import poll_labels
from backend.models.user import User


@pytest.mark.asyncio
async def test_topics_overview_no_dupes_even_when_ws(db_session: AsyncSession, test_user: User):
    """Test that overview API returns unique IDs even when simulating WebSocket updates."""
    
    # Create a label
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    db_session.add(label)
    await db_session.commit()
    
    # Create a poll
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    
    # Insert poll-label relationship
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Test the API endpoint
    from backend.api.labels import get_label_overview
    from fastapi import Request, Response
    
    class MockRequest:
        headers = {}
    
    class MockResponse:
        def __init__(self):
            self.headers = {}
            self.status_code = 200
    
    request = MockRequest()
    response = MockResponse()
    
    # First call - should return the poll
    result1 = await get_label_overview(
        slug="test-label",
        tab="all",
        page=1,
        per_page=12,
        sort="newest",
        request=request,
        response=response,
        db=db_session,
        current_user=test_user
    )
    
    # Verify first response
    assert result1 is not None
    assert "items" in result1
    assert len(result1["items"]) == 1
    assert result1["items"][0]["id"] == str(poll.id)
    
    # Simulate a "WebSocket update" by calling the same endpoint again
    # This simulates what would happen if a WebSocket message triggered a refetch
    result2 = await get_label_overview(
        slug="test-label",
        tab="all",
        page=1,
        per_page=12,
        sort="newest",
        request=request,
        response=response,
        db=db_session,
        current_user=test_user
    )
    
    # Verify second response is identical and has no duplicates
    assert result2 is not None
    assert "items" in result2
    assert len(result2["items"]) == 1
    assert result2["items"][0]["id"] == str(poll.id)
    
    # Verify no duplicates in either response
    ids1 = [item["id"] for item in result1["items"]]
    ids2 = [item["id"] for item in result2["items"]]
    
    assert len(ids1) == len(set(ids1)), "First response should have no duplicate IDs"
    assert len(ids2) == len(set(ids2)), "Second response should have no duplicate IDs"
    
    # Verify responses are identical
    assert ids1 == ids2, "Responses should be identical"


@pytest.mark.asyncio
async def test_topics_overview_sort_after_merge(db_session: AsyncSession, test_user: User):
    """Test that final result is sorted and deduped when merging sublists."""
    
    # Create a label
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    db_session.add(label)
    await db_session.commit()
    
    # Create multiple polls with different creation times
    from datetime import datetime, timedelta
    
    poll1 = Poll(
        id=uuid4(),
        title="Old Poll",
        decision_type="level_a",
        created_by=test_user.id,
        created_at=datetime.now() - timedelta(days=2)
    )
    poll2 = Poll(
        id=uuid4(),
        title="New Poll",
        decision_type="level_b",
        created_by=test_user.id,
        created_at=datetime.now() - timedelta(days=1)
    )
    poll3 = Poll(
        id=uuid4(),
        title="Latest Poll",
        decision_type="level_a",
        created_by=test_user.id,
        created_at=datetime.now()
    )
    
    db_session.add_all([poll1, poll2, poll3])
    await db_session.commit()
    
    # Insert poll-label relationships
    for poll in [poll1, poll2, poll3]:
        await db_session.execute(
            poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
        )
    await db_session.commit()
    
    # Test the API endpoint with "all" tab (which would merge level_a and level_b)
    from backend.api.labels import get_label_overview
    from fastapi import Request, Response
    
    class MockRequest:
        headers = {}
    
    class MockResponse:
        def __init__(self):
            self.headers = {}
            self.status_code = 200
    
    request = MockRequest()
    response = MockResponse()
    
    # Test "all" tab with newest sort
    result = await get_label_overview(
        slug="test-label",
        tab="all",
        page=1,
        per_page=12,
        sort="newest",
        request=request,
        response=response,
        db=db_session,
        current_user=test_user
    )
    
    # Verify response
    assert result is not None
    assert "items" in result
    assert len(result["items"]) == 3, "Should return all 3 polls"
    
    # Verify no duplicates
    ids = [item["id"] for item in result["items"]]
    assert len(ids) == len(set(ids)), "Should have no duplicate IDs"
    
    # Verify sorting (newest first)
    assert ids[0] == str(poll3.id), "Latest poll should be first"
    assert ids[1] == str(poll2.id), "New poll should be second"
    assert ids[2] == str(poll1.id), "Old poll should be last"
    
    # Test with oldest sort
    result_oldest = await get_label_overview(
        slug="test-label",
        tab="all",
        page=1,
        per_page=12,
        sort="oldest",
        request=request,
        response=response,
        db=db_session,
        current_user=test_user
    )
    
    # Verify oldest sorting
    ids_oldest = [item["id"] for item in result_oldest["items"]]
    assert len(ids_oldest) == len(set(ids_oldest)), "Should have no duplicate IDs"
    assert ids_oldest[0] == str(poll1.id), "Oldest poll should be first"
    assert ids_oldest[1] == str(poll2.id), "New poll should be second"
    assert ids_oldest[2] == str(poll3.id), "Latest poll should be last"


@pytest.mark.asyncio
async def test_topics_overview_debug_endpoint(db_session: AsyncSession, test_user: User):
    """Test the debug endpoint returns correct data."""
    
    # Create a label
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    db_session.add(label)
    await db_session.commit()
    
    # Create polls
    poll1 = Poll(
        id=uuid4(),
        title="Principle Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    poll2 = Poll(
        id=uuid4(),
        title="Action Poll",
        decision_type="level_b",
        created_by=test_user.id
    )
    
    db_session.add_all([poll1, poll2])
    await db_session.commit()
    
    # Insert poll-label relationships
    for poll in [poll1, poll2]:
        await db_session.execute(
            poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
        )
    await db_session.commit()
    
    # Test the debug endpoint
    from backend.api.labels import get_label_raw_debug
    
    result = await get_label_raw_debug(
        slug="test-label",
        db=db_session,
        current_user=test_user
    )
    
    # Verify response structure
    assert "ids" in result
    assert "counts" in result
    assert "duplicates" in result
    
    # Verify counts
    assert result["counts"]["level_a"] == 1
    assert result["counts"]["level_b"] == 1
    assert result["counts"]["all"] == 2
    
    # Verify IDs
    assert str(poll1.id) in result["ids"]["level_a"]
    assert str(poll2.id) in result["ids"]["level_b"]
    assert str(poll1.id) in result["ids"]["all"]
    assert str(poll2.id) in result["ids"]["all"]
    
    # Verify no duplicates
    assert len(result["duplicates"]["level_a"]) == 0
    assert len(result["duplicates"]["level_b"]) == 0
    assert len(result["duplicates"]["all"]) == 0
