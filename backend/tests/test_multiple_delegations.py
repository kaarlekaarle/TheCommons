import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions.delegation import (
    DelegationAlreadyExistsError,
    DelegationChainError,
    DelegationLimitExceededError,
    InvalidDelegationPeriodError,
    PostVoteDelegationError,
    SelfDelegationError,
)
from backend.models import Option, Poll, User, Vote
from backend.models.delegation import Delegation
from backend.services.delegation import DelegationService


@pytest.mark.asyncio
async def test_multiple_delegations_to_different_users(
    db_session, test_user, test_user2, test_user3
):
    """Test creating multiple delegations to different users."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create first delegation
    delegation1 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,  # Make it indefinite
        poll_id=None,
    )

    # Create second delegation to different user
    delegation2 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,  # Make it indefinite
        poll_id=None,
    )

    # Verify both delegations are active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 2
    assert any(d.id == delegation1.id for d in active_delegations)
    assert any(d.id == delegation2.id for d in active_delegations)


@pytest.mark.asyncio
async def test_multiple_delegations_same_user_different_periods(
    db_session, test_user, test_user2
):
    """Test creating multiple delegations to the same user but different time periods."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create first delegation
    delegation1 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=now + timedelta(days=30),
        poll_id=None,
    )

    # Create second delegation to same user but different period
    delegation2 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now + timedelta(days=31),
        end_date=now + timedelta(days=60),
        poll_id=None,
    )

    # Only the first should be active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 1, (
        f"Expected 1 active delegation, got {len(active_delegations)}: "
        f"{active_delegations}"
    )
    assert active_delegations[0].id == delegation1.id

    # Both should exist in all_delegations
    all_delegations = await db_session.execute(
        select(Delegation).where(Delegation.delegator_id == test_user.id)
    )
    all_delegations = all_delegations.scalars().all()
    assert len(all_delegations) == 2
    assert any(d.id == delegation1.id for d in all_delegations)
    assert any(d.id == delegation2.id for d in all_delegations)


@pytest.mark.asyncio
async def test_multiple_delegations_same_user_overlapping_periods(
    db_session, test_user, test_user2
):
    """Test that overlapping delegations to the same user are not allowed."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create first delegation
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=now + timedelta(days=30),
        poll_id=None,
    )

    # Try to create overlapping delegation to same user
    with pytest.raises(DelegationAlreadyExistsError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now + timedelta(days=15),  # Overlaps with first delegation
            end_date=now + timedelta(days=45),
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_multiple_delegations_poll_specific_and_global(
    db_session, test_user, test_user2, test_user3, test_poll
):
    """Test creating both poll-specific and global delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create global delegation
    global_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Create poll-specific delegation
    poll_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=test_poll.id,
    )

    # Verify both delegations are active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 2
    assert any(d.id == global_delegation.id for d in active_delegations)
    assert any(d.id == poll_delegation.id for d in active_delegations)


@pytest.mark.asyncio
async def test_multiple_delegations_chain_resolution(
    db_session, test_user, test_user2, test_user3, test_user4
):
    """Test chain resolution with multiple delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create multiple delegation chains
    # Chain 1: user -> user2 -> user3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Chain 2: user -> user4
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user4.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Verify chain resolution uses most recent delegation
    final_delegatee = await service.resolve_delegation_chain(test_user.id, None)
    assert final_delegatee == test_user4.id, (
        "Should resolve to user4 as it's the most recent"
    )

    # Test chain resolution with path
    final_delegatee, path = await service.resolve_delegation_chain(
        test_user.id, None, include_path=True
    )
    assert final_delegatee == test_user4.id
    assert len(path) == 2
    assert path == [test_user.id, test_user4.id]


@pytest.mark.asyncio
async def test_multiple_delegations_stats(
    db_session, test_user, test_user2, test_user3
):
    """Test stats calculation with multiple delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create multiple delegations
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Get stats
    stats = await service.get_delegation_stats()
    assert stats["active_delegations"] == 2
    assert len(stats["top_delegatees"]) >= 2
    assert any(d["user_id"] == str(test_user2.id) for d in stats["top_delegatees"])
    assert any(d["user_id"] == str(test_user3.id) for d in stats["top_delegatees"])


@pytest.mark.asyncio
async def test_multiple_delegations_revocation(
    db_session, test_user, test_user2, test_user3
):
    """Test revoking one of multiple delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create multiple delegations
    delegation1 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    delegation2 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Revoke first delegation
    await service.revoke_delegation(delegation1.id)

    # Verify only second delegation is active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 1
    assert active_delegations[0].id == delegation2.id


@pytest.mark.asyncio
async def test_delegation_limit(
    db_session, test_user, test_user2, test_user3, test_user4, test_user5, test_user6
):
    """Test that users cannot exceed the maximum number of active delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create 5 delegations (maximum allowed)
    for delegatee in [test_user2, test_user3, test_user4, test_user5, test_user6]:
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=delegatee.id,
            start_date=now,
            end_date=None,
            poll_id=None,
        )

    # Verify we have 5 active delegations
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 5

    # Try to create a 6th delegation
    with pytest.raises(DelegationLimitExceededError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,  # Reusing test_user2 as delegatee
            start_date=now,
            end_date=None,
            poll_id=None,
        )

    # Verify we still have only 5 delegations
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 5


@pytest.mark.asyncio
async def test_delegation_expiration(db_session, test_user, test_user2):
    """Test that delegations expire after their end date."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create a delegation with a short expiration time
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=now + timedelta(seconds=1),  # Expires in 1 second
        poll_id=None,
    )

    # Verify delegation is active initially
    active_delegations = await service.get_active_delegations(test_user.id)
    assert (
        len(active_delegations) == 1
    ), f"Expected 1 active delegation, got {len(active_delegations)}: {active_delegations}"
    assert active_delegations[0].id == delegation.id

    # Wait for delegation to expire
    await asyncio.sleep(2)

    # Verify delegation is no longer active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert (
        len(active_delegations) == 0
    ), f"Expected 0 active delegations, got {len(active_delegations)}: {active_delegations}"

    # Verify delegation still exists in history
    all_delegations = await db_session.execute(
        select(Delegation).where(Delegation.delegator_id == test_user.id)
    )
    all_delegations = all_delegations.scalars().all()
    assert len(all_delegations) == 1
    assert all_delegations[0].id == delegation.id
    assert all_delegations[0].end_date is not None


@pytest.mark.asyncio
async def test_delegation_updates(db_session, test_user, test_user2, test_user3):
    """Test updating delegation by revoking and creating a new one."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create initial delegation
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    # Revoke the delegation
    await service.revoke_delegation(delegation.id)
    # Create a new delegation to a different user
    new_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    # Verify only the new delegation is active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 1
    assert active_delegations[0].id == new_delegation.id
    assert active_delegations[0].delegatee_id == test_user3.id


@pytest.mark.asyncio
async def test_delegation_history(db_session, test_user, test_user2):
    """Test tracking delegation history."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create and revoke multiple delegations
    delegations = []
    for i in range(3):
        delegation = await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now + timedelta(days=i * 30),
            end_date=now + timedelta(days=(i + 1) * 30),
            poll_id=None,
        )
        delegations.append(delegation)

        # Revoke after a short delay
        await asyncio.sleep(1)
        await service.revoke_delegation(delegation.id)

    # Verify all delegations are in history
    all_delegations = await db_session.execute(
        select(Delegation).where(Delegation.delegator_id == test_user.id)
    )
    history = all_delegations.scalars().all()
    assert len(history) == 3

    # Verify none are active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 0

    # Verify end dates are set
    for delegation in history:
        assert delegation.end_date is not None


@pytest.mark.asyncio
async def test_concurrent_delegations(db_session, test_user, test_user2, test_user3):
    """Test handling of concurrent delegation operations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    async def create_delegation(delegatee_id):
        try:
            return await service.create_delegation(
                delegator_id=test_user.id,
                delegatee_id=delegatee_id,
                start_date=now,
                end_date=None,
                poll_id=None,
            )
        except Exception as e:
            return e

    # Give the DB a moment to be ready for concurrent writes
    await asyncio.sleep(0.1)
    # Create multiple delegations concurrently
    tasks = [create_delegation(test_user2.id), create_delegation(test_user3.id)]
    results = await asyncio.gather(*tasks)

    # Verify all delegations were created successfully
    active_delegations = await service.get_active_delegations(test_user.id)
    assert (
        len(active_delegations) == 2
    ), f"Expected 2 active delegations, got {len(active_delegations)}: {active_delegations}"
    # Note: SQLite may not support true concurrency; this test may fail on SQLite.

    # Verify both delegatees are present
    delegatee_ids = {d.delegatee_id for d in active_delegations}
    assert test_user2.id in delegatee_ids
    assert test_user3.id in delegatee_ids


@pytest.mark.asyncio
async def test_delegation_error_conditions(db_session, test_user, test_user2):
    """Test various error conditions in delegation creation."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Test self-delegation
    with pytest.raises(SelfDelegationError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user.id,
            start_date=now,
            end_date=None,
            poll_id=None,
        )

    # Test delegation to deleted user
    test_user2.is_deleted = True
    test_user2.deleted_at = now
    await db_session.commit()

    with pytest.raises(ValueError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now,
            end_date=None,
            poll_id=None,
        )

    # Verify user2 is deleted
    assert test_user2.is_deleted is True
    assert test_user2.deleted_at is not None

    # Test delegation with invalid dates
    with pytest.raises(InvalidDelegationPeriodError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now + timedelta(days=1),
            end_date=now,
            poll_id=None,
        )

    # Test delegation after voting
    poll = await create_test_poll(db_session, test_user)
    await create_test_vote(db_session, test_user.id, poll.id)

    with pytest.raises(PostVoteDelegationError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now,
            end_date=None,
            poll_id=poll.id,
        )


@pytest.mark.asyncio
async def test_delegation_edge_cases(db_session, test_user, test_user2, test_user3):
    """Test edge cases in delegation handling."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Test delegation with same start and end date
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=now,
        poll_id=None,
    )

    # Verify delegation is active
    assert delegation.is_active is True
    assert delegation.start_date == now
    assert delegation.end_date == now

    # Test delegation with very long period
    long_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=now + timedelta(days=3650),  # 10 years
        poll_id=None,
    )

    # Verify long delegation is active
    assert long_delegation.is_active is True
    assert long_delegation.start_date == now
    assert long_delegation.end_date == now + timedelta(days=3650)

    # Test delegation with very short period
    short_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=now + timedelta(seconds=1),
        poll_id=None,
    )

    # Verify short delegation is active
    assert short_delegation.is_active is True
    assert short_delegation.start_date == now
    assert short_delegation.end_date == now + timedelta(seconds=1)


@pytest.mark.asyncio
async def test_delegation_performance(db_session, test_user, test_user2):
    """Test performance aspects of delegation operations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Test creating multiple delegations quickly
    start_time = datetime.utcnow()
    for i in range(5):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=now + timedelta(days=i),
            end_date=now + timedelta(days=i + 1),
            poll_id=None,
        )
    end_time = datetime.utcnow()
    creation_time = (end_time - start_time).total_seconds()
    assert creation_time < 1.0  # Should complete within 1 second

    # Test querying active delegations performance
    start_time = datetime.utcnow()
    for _ in range(10):
        active_delegations = await service.get_active_delegations(test_user.id)
        assert len(active_delegations) <= 1  # Only one should be active at a time
    end_time = datetime.utcnow()
    query_time = (end_time - start_time).total_seconds()
    assert query_time < 0.5  # Should complete within 0.5 seconds


@pytest.mark.asyncio
async def test_delegation_chain_complexity(
    db_session, test_user, test_user2, test_user3, test_user4
):
    """Test complex delegation chain scenarios."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create a complex delegation chain
    # user -> user2 -> user3 -> user4
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )
    await service.create_delegation(
        delegator_id=test_user3.id,
        delegatee_id=test_user4.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Test chain resolution
    final_delegatee = await service.resolve_delegation_chain(test_user.id, None)
    assert final_delegatee == test_user4.id

    # Test chain resolution with max depth
    with pytest.raises(DelegationChainError):
        await service.resolve_delegation_chain(test_user.id, None, max_depth=2)

    # Test chain resolution with path
    final_delegatee, path = await service.resolve_delegation_chain(
        test_user.id, None, include_path=True
    )
    assert final_delegatee == test_user4.id
    assert len(path) == 4
    assert path == [test_user.id, test_user2.id, test_user3.id, test_user4.id]


@pytest.mark.asyncio
async def test_delegation_stats_complexity(
    db_session, test_user, test_user2, test_user3
):
    """Test complex delegation statistics."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create multiple delegations with different patterns
    # User1 delegates to User2
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # User2 delegates to User3
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # User1 also delegates to User3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Get stats
    stats = await service.get_delegation_stats()

    # Verify stats
    assert stats["active_delegations"] == 3
    assert len(stats["top_delegatees"]) >= 2

    # Verify User3 is the top delegatee
    top_delegatee = stats["top_delegatees"][0]
    assert top_delegatee["user_id"] == str(test_user3.id)
    assert top_delegatee["count"] >= 2  # User3 has at least 2 delegations

    # Verify chain statistics
    assert stats["avg_chain_length"] > 1  # Should have some chains
    assert stats["longest_chain"] >= 2  # Should have at least one chain of length 2


# Helper functions for test setup
async def create_test_poll(db_session, user):
    """Create a test poll."""
    poll = Poll(
        title="Test Poll",
        description="Test Poll Description",
        created_at=datetime.utcnow(),
        created_by=user.id,
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    return poll


async def create_test_vote(db_session, user_id, poll_id):
    """Create a test vote."""
    # First create a test option
    option = Option(text="Test Option", poll_id=poll_id, created_at=datetime.utcnow())
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    # Then create the vote with the option
    vote = Vote(
        user_id=user_id,
        poll_id=poll_id,
        option_id=option.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    return vote
