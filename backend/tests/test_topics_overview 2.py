import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.poll import Poll
from backend.models.label import Label
from backend.models.poll_label import poll_labels
from backend.models.user import User


@pytest.mark.asyncio
async def test_overview_no_duplicate_polls(db_session: AsyncSession, test_user: User):
    """Test that overview API returns each poll only once even with duplicate poll-label relationships."""
    
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
    
    # Insert poll-label relationship (only one allowed due to unique constraint)
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Verify we have the relationship in the database
    result = await db_session.execute(
        select(poll_labels).where(
            (poll_labels.c.poll_id == poll.id) & 
            (poll_labels.c.label_id == label.id)
        )
    )
    relationships = result.fetchall()
    assert len(relationships) == 1, "Should have one poll-label relationship"
    
    # Test the API endpoint
    from backend.api.labels import get_label_overview
    from fastapi import Request, Response
    
    # Mock request and response
    class MockRequest:
        headers = {}
    
    class MockResponse:
        def __init__(self):
            self.headers = {}
            self.status_code = 200
    
    request = MockRequest()
    response = MockResponse()
    
    # Call the API
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
    
    # Verify the response
    assert result is not None
    assert "items" in result
    assert len(result["items"]) == 1, "Should return exactly one poll"
    assert result["items"][0]["id"] == str(poll.id)
    assert result["items"][0]["title"] == "Test Poll"


@pytest.mark.asyncio
async def test_overview_counts_correct_with_duplicates(db_session: AsyncSession, test_user: User):
    """Test that counts are correct even with duplicate poll-label relationships."""
    
    # Create a label
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    db_session.add(label)
    await db_session.commit()
    
    # Create multiple polls
    poll1 = Poll(
        id=uuid4(),
        title="Test Poll 1",
        decision_type="level_a",
        created_by=test_user.id
    )
    poll2 = Poll(
        id=uuid4(),
        title="Test Poll 2",
        decision_type="level_b",
        created_by=test_user.id
    )
    db_session.add_all([poll1, poll2])
    await db_session.commit()
    
    # Insert poll-label relationships (unique constraint prevents duplicates)
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll1.id, label_id=label.id)
    )
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll2.id, label_id=label.id)
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
    
    # Test "all" tab
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
    
    # Verify counts are correct (should count unique polls, not relationships)
    assert result["counts"]["level_a"] == 1, "Should count 1 level_a poll"
    assert result["counts"]["level_b"] == 1, "Should count 1 level_b poll"
    assert result["counts"]["total"] == 2, "Should count 2 total polls"
    assert result["page"]["total"] == 2, "Should have 2 total items"
    assert len(result["items"]) == 2, "Should return 2 unique polls"


@pytest.mark.asyncio
async def test_overview_pagination_with_duplicates(db_session: AsyncSession, test_user: User):
    """Test that pagination works correctly with duplicate poll-label relationships."""
    
    # Create a label
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    db_session.add(label)
    await db_session.commit()
    
    # Create multiple polls
    polls = []
    for i in range(5):
        poll = Poll(
            id=uuid4(),
            title=f"Test Poll {i}",
            decision_type="level_a",
            created_by=test_user.id
        )
        polls.append(poll)
    
    db_session.add_all(polls)
    await db_session.commit()
    
    # Insert poll-label relationships (unique constraint prevents duplicates)
    for poll in polls:
        await db_session.execute(
            poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
        )
    
    await db_session.commit()
    
    # Test the API endpoint with pagination
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
    
    # Test first page
    result = await get_label_overview(
        slug="test-label",
        tab="all",
        page=1,
        per_page=3,
        sort="newest",
        request=request,
        response=response,
        db=db_session,
        current_user=test_user
    )
    
    # Verify pagination
    assert result["page"]["total"] == 5, "Should have 5 total unique polls"
    assert result["page"]["total_pages"] == 2, "Should have 2 pages"
    assert len(result["items"]) == 3, "Should return 3 polls on first page"
    
    # Verify no duplicates in response
    poll_ids = [item["id"] for item in result["items"]]
    assert len(poll_ids) == len(set(poll_ids)), "Should have no duplicate poll IDs in response"
