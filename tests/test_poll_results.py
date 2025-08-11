"""Tests for poll results endpoint with delegation support."""

import pytest
from datetime import datetime, timedelta

from backend.services.delegation import DelegationService
from backend.core.auth import create_access_token, get_current_active_user
from backend.services.poll import get_poll_results
from tests.utils import create_test_user, create_test_poll_with_options


@pytest.mark.asyncio
async def test_poll_results_direct(db_session):
    """
    Direct test for poll results service function without complex infrastructure.
    """
    # Create test users directly
    from backend.models.user import User
    from backend.core.auth import get_password_hash
    
    alice = User(
        username="alice",
        email="alice@test.com",
        hashed_password=get_password_hash("alice123")
    )
    db_session.add(alice)
    await db_session.commit()
    await db_session.refresh(alice)
    
    bob = User(
        username="bob",
        email="bob@test.com",
        hashed_password=get_password_hash("bob123")
    )
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)
    
    # Create a poll directly
    from backend.models.poll import Poll
    
    poll = Poll(
        title="Test Poll",
        description="A test poll for delegation voting",
        created_by=alice.id,
        status="DRAFT",
        visibility="PUBLIC",
        allow_delegation=True,
        require_authentication=True,
        max_votes_per_user=1
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Create options directly
    from backend.models.option import Option
    
    option_a = Option(
        text="Option A",
        poll_id=poll.id,
        order=0
    )
    db_session.add(option_a)
    
    option_b = Option(
        text="Option B",
        poll_id=poll.id,
        order=1
    )
    db_session.add(option_b)
    await db_session.commit()
    await db_session.refresh(option_a)
    await db_session.refresh(option_b)
    
    # Create a vote directly
    from backend.models.vote import Vote
    
    vote = Vote(
        user_id=alice.id,
        poll_id=poll.id,
        option_id=option_a.id,
        weight=1
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    
    # Test the poll results service function directly
    results = await get_poll_results(poll.id, db_session)
    
    # Verify we have results for both options
    assert len(results) == 2
    
    # Find Option A and Option B in results
    option_a_result = None
    option_b_result = None
    
    for result in results:
        if result.text == "Option A":
            option_a_result = result
        elif result.text == "Option B":
            option_b_result = result
    
    assert option_a_result is not None, "Option A result not found"
    assert option_b_result is not None, "Option B result not found"
    
    # Assert the expected vote counts
    # Option A should have 1 direct vote (Alice)
    assert option_a_result.direct_votes == 1, f"Expected 1 direct vote, got {option_a_result.direct_votes}"
    assert option_a_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_a_result.delegated_votes}"
    assert option_a_result.total_votes == 1, f"Expected 1 total votes, got {option_a_result.total_votes}"
    
    # Option B should have 0 votes
    assert option_b_result.direct_votes == 0, f"Expected 0 direct votes, got {option_b_result.direct_votes}"
    assert option_b_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_b_result.delegated_votes}"
    assert option_b_result.total_votes == 0, f"Expected 0 total votes, got {option_b_result.total_votes}"


@pytest.mark.asyncio
async def test_poll_results_simple(db_session):
    """
    Simple test for poll results service function.
    """
    # Create test users directly in the same session
    alice = await create_test_user(
        db_session,
        username="alice",
        email="alice@test.com",
        password="alice123"
    )
    
    bob = await create_test_user(
        db_session,
        username="bob",
        email="bob@test.com",
        password="bob123"
    )
    
    # Create a test poll with two options in the same session
    poll, options = await create_test_poll_with_options(
        db_session,
        alice,
        title="Test Poll",
        description="A test poll for delegation voting",
        options=["Option A", "Option B"]
    )
    
    option_a, option_b = options
    
    # Create a vote directly
    from backend.models.vote import Vote
    
    vote = Vote(
        user_id=alice.id,
        poll_id=poll.id,
        option_id=option_a.id,
        weight=1
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    
    # Test the poll results service function directly
    results = await get_poll_results(poll.id, db_session)
    
    # Verify we have results for both options
    assert len(results) == 2
    
    # Find Option A and Option B in results
    option_a_result = None
    option_b_result = None
    
    for result in results:
        if result.text == "Option A":
            option_a_result = result
        elif result.text == "Option B":
            option_b_result = result
    
    assert option_a_result is not None, "Option A result not found"
    assert option_b_result is not None, "Option B result not found"
    
    # Assert the expected vote counts
    # Option A should have 1 direct vote (Alice)
    assert option_a_result.direct_votes == 1, f"Expected 1 direct vote, got {option_a_result.direct_votes}"
    assert option_a_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_a_result.delegated_votes}"
    assert option_a_result.total_votes == 1, f"Expected 1 total votes, got {option_a_result.total_votes}"
    
    # Option B should have 0 votes
    assert option_b_result.direct_votes == 0, f"Expected 0 direct votes, got {option_b_result.direct_votes}"
    assert option_b_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_b_result.delegated_votes}"
    assert option_b_result.total_votes == 0, f"Expected 0 total votes, got {option_b_result.total_votes}"


@pytest.mark.asyncio
async def test_poll_results_service_with_delegation(db_session):
    """
    Test poll results service function directly with delegation support.
    
    Scenario:
    1. Alice creates a poll with two options
    2. Bob delegates to Alice for that poll
    3. Alice votes for Option A
    4. Check that Option A has 1 direct vote + 1 delegated vote = 2 total votes
    """
    # Create test users directly in the same session
    alice = await create_test_user(
        db_session,
        username="alice",
        email="alice@test.com",
        password="alice123"
    )
    
    bob = await create_test_user(
        db_session,
        username="bob",
        email="bob@test.com",
        password="bob123"
    )
    
    # Create a test poll with two options in the same session
    poll, options = await create_test_poll_with_options(
        db_session,
        alice,
        title="Test Poll",
        description="A test poll for delegation voting",
        options=["Option A", "Option B"]
    )
    
    option_a, option_b = options
    
    # Step 1: Bob delegates to Alice for this poll
    delegation_service = DelegationService(db_session)
    delegation = await delegation_service.create_delegation(
        delegator_id=bob.id,
        delegatee_id=alice.id,
        poll_id=poll.id,
        start_date=datetime.utcnow(),
        end_date=None
    )
    
    # Verify delegation was created
    assert delegation is not None
    assert delegation.delegator_id == bob.id
    assert delegation.delegatee_id == alice.id
    assert delegation.poll_id == poll.id
    
    # Step 2: Alice votes for Option A by creating the vote directly in the database
    # Since the API authentication is complex in tests, let's create the vote directly
    from backend.models.vote import Vote
    from backend.core.voting import create_vote
    
    vote_data = {
        "poll_id": poll.id,
        "option_id": option_a.id,
        "user_id": alice.id,
        "weight": 1
    }
    
    vote = await create_vote(db_session, vote_data, alice)
    assert vote is not None
    assert vote.user_id == alice.id
    assert vote.option_id == option_a.id
    assert vote.poll_id == poll.id
    
    # Step 3: Test the poll results service function directly
    results = await get_poll_results(poll.id, db_session)
    
    # Verify we have results for both options
    assert len(results) == 2
    
    # Find Option A and Option B in results
    option_a_result = None
    option_b_result = None
    
    for result in results:
        if result.text == "Option A":
            option_a_result = result
        elif result.text == "Option B":
            option_b_result = result
    
    assert option_a_result is not None, "Option A result not found"
    assert option_b_result is not None, "Option B result not found"
    
    # Step 4: Assert the expected vote counts
    # Option A should have 1 direct vote (Alice) + 1 delegated vote (Bob) = 2 total
    assert option_a_result.direct_votes == 1, f"Expected 1 direct vote, got {option_a_result.direct_votes}"
    assert option_a_result.delegated_votes == 1, f"Expected 1 delegated vote, got {option_a_result.delegated_votes}"
    assert option_a_result.total_votes == 2, f"Expected 2 total votes, got {option_a_result.total_votes}"
    
    # Option B should have 0 votes
    assert option_b_result.direct_votes == 0, f"Expected 0 direct votes, got {option_b_result.direct_votes}"
    assert option_b_result.delegated_votes == 0, f"Expected 0 delegated votes, got {option_b_result.delegated_votes}"
    assert option_b_result.total_votes == 0, f"Expected 0 total votes, got {option_b_result.total_votes}"
    
    # Verify results are sorted by total votes (descending)
    assert results[0].total_votes >= results[1].total_votes


@pytest.mark.asyncio
async def test_poll_results_with_delegation(client, db_session):
    """
    Test poll results with delegation support.
    
    Scenario:
    1. Alice creates a poll with two options
    2. Bob delegates to Alice for that poll
    3. Alice votes for Option A
    4. Check that Option A has 1 direct vote + 1 delegated vote = 2 total votes
    """
    # Create test users directly in the same session as the test client
    alice = await create_test_user(
        db_session,
        username="alice",
        email="alice@test.com",
        password="alice123"
    )
    
    bob = await create_test_user(
        db_session,
        username="bob",
        email="bob@test.com",
        password="bob123"
    )
    
    # Create a test poll with two options in the same session
    poll, options = await create_test_poll_with_options(
        db_session,
        alice,
        title="Test Poll",
        description="A test poll for delegation voting",
        options=["Option A", "Option B"]
    )
    
    option_a, option_b = options
    
    # Step 1: Bob delegates to Alice for this poll
    delegation_service = DelegationService(db_session)
    delegation = await delegation_service.create_delegation(
        delegator_id=bob.id,
        delegatee_id=alice.id,
        poll_id=poll.id,
        start_date=datetime.utcnow(),
        end_date=None
    )
    
    # Verify delegation was created
    assert delegation is not None
    assert delegation.delegator_id == bob.id
    assert delegation.delegatee_id == alice.id
    assert delegation.poll_id == poll.id
    
    # Step 2: Alice votes for Option A by creating the vote directly in the database
    # Since the API authentication is complex in tests, let's create the vote directly
    from backend.models.vote import Vote
    from backend.core.voting import create_vote
    
    vote_data = {
        "poll_id": poll.id,
        "option_id": option_a.id,
        "user_id": alice.id,
        "weight": 1
    }
    
    vote = await create_vote(db_session, vote_data, alice)
    assert vote is not None
    assert vote.user_id == alice.id
    assert vote.option_id == option_a.id
    assert vote.poll_id == poll.id
    
    # Create authentication headers for Alice
    access_token = create_access_token(
        data={"sub": str(alice.id)},
        expires_delta=timedelta(minutes=30),
    )
    alice_auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 3: Override the authentication dependency for the test client
    from backend.main import app
    from backend.core.auth import get_current_active_user
    
    async def override_get_current_user():
        return alice
    
    app.dependency_overrides[get_current_active_user] = override_get_current_user
    
    try:
        # Step 4: Get poll results
        results_response = await client.get(
            f"/api/polls/{poll.id}/results",
            headers=alice_auth_headers
        )
        
        assert results_response.status_code == 200
        results = results_response.json()
        
        # Verify we have results for both options
        assert len(results) == 2
        
        # Find Option A and Option B in results
        option_a_result = None
        option_b_result = None
        
        for result in results:
            if result["text"] == "Option A":
                option_a_result = result
            elif result["text"] == "Option B":
                option_b_result = result
        
        assert option_a_result is not None, "Option A result not found"
        assert option_b_result is not None, "Option B result not found"
        
        # Step 5: Assert the expected vote counts
        # Option A should have 1 direct vote (Alice) + 1 delegated vote (Bob) = 2 total
        assert option_a_result["direct_votes"] == 1, f"Expected 1 direct vote, got {option_a_result['direct_votes']}"
        assert option_a_result["delegated_votes"] == 1, f"Expected 1 delegated vote, got {option_a_result['delegated_votes']}"
        assert option_a_result["total_votes"] == 2, f"Expected 2 total votes, got {option_a_result['total_votes']}"
        
        # Option B should have 0 votes
        assert option_b_result["direct_votes"] == 0, f"Expected 0 direct votes, got {option_b_result['direct_votes']}"
        assert option_b_result["delegated_votes"] == 0, f"Expected 0 delegated votes, got {option_b_result['delegated_votes']}"
        assert option_b_result["total_votes"] == 0, f"Expected 0 total votes, got {option_b_result['total_votes']}"
        
        # Verify results are sorted by total votes (descending)
        assert results[0]["total_votes"] >= results[1]["total_votes"]
        
    finally:
        # Clean up the dependency override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_poll_results_unauthorized(client, db_session):
    """
    Test poll results endpoint requires authentication.
    """
    # Create a test user and poll
    alice = await create_test_user(
        db_session,
        username="alice",
        email="alice@test.com",
        password="alice123"
    )
    
    poll, _ = await create_test_poll_with_options(
        db_session,
        alice,
        title="Test Poll",
        description="A test poll",
        options=["Option A", "Option B"]
    )
    
    # Try to get results without authentication
    results_response = await client.get(f"/api/polls/{poll.id}/results")
    
    assert results_response.status_code == 401


@pytest.mark.asyncio
async def test_poll_results_poll_not_found(client, db_session):
    """
    Test poll results with non-existent poll ID.
    """
    # Create a test user for authentication
    alice = await create_test_user(
        db_session,
        username="alice",
        email="alice@test.com",
        password="alice123"
    )
    
    # Create authentication headers
    access_token = create_access_token(
        data={"sub": str(alice.id)},
        expires_delta=timedelta(minutes=30),
    )
    alice_auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    fake_poll_id = "00000000-0000-0000-0000-000000000000"
    
    results_response = await client.get(
        f"/api/polls/{fake_poll_id}/results",
        headers=alice_auth_headers
    )
    
    assert results_response.status_code == 404
    assert "not found" in results_response.json()["message"].lower()
