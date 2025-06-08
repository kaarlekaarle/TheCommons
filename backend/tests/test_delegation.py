print("RUNNING backend/tests/test_delegation.py")
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    DelegationError,
    DelegationNotFoundError,
    InvalidDelegationPeriodError,
    SelfDelegationError,
)
from backend.core.security import get_password_hash
from backend.models.delegation import Delegation
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote
from backend.services.delegation import DelegationService


@pytest.mark.asyncio
async def test_create_delegation(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    delegation = Delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        poll_id=None,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    db_session.add(delegation)
    await db_session.commit()
    await db_session.refresh(delegation)
    assert delegation.delegator_id == test_user.id
    assert delegation.delegatee_id == test_user2.id
    assert delegation.revoked_at is None


@pytest.mark.asyncio
async def test_self_delegation_prevention(db_session: AsyncSession, test_user: User):
    service = DelegationService(db_session)
    with pytest.raises(SelfDelegationError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user.id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_duplicate_delegation_prevention(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)
    # Create first delegation
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    # Try to create duplicate
    with pytest.raises(DelegationAlreadyExistsError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_circular_delegation_prevention(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)
    # Create first delegation
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    # Try to create circular delegation
    with pytest.raises(CircularDelegationError):
        await service.create_delegation(
            delegator_id=test_user2.id,
            delegatee_id=test_user.id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_revoke_delegation(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)
    # Create delegation
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    # Revoke delegation
    await service.revoke_delegation(delegation.id)
    await db_session.refresh(delegation)
    assert delegation.revoked_at is not None


@pytest.mark.asyncio
async def test_poll_specific_delegation(
    db_session: AsyncSession, test_user: User, test_user2: User, test_poll: Poll
):
    service = DelegationService(db_session)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        poll_id=test_poll.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    assert delegation.poll_id == test_poll.id


@pytest.mark.asyncio
async def test_delegation_after_voting(
    db_session: AsyncSession, test_user: User, test_user2: User, test_poll: Poll
):
    service = DelegationService(db_session)

    # Create an option for the poll
    option = Option(poll_id=test_poll.id, text="Test Option")
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    # Create a vote with the option
    vote = Vote(user_id=test_user.id, poll_id=test_poll.id, option_id=option.id)
    db_session.add(vote)
    await db_session.commit()

    # Try to create delegation after voting
    with pytest.raises(DelegationError, match="Cannot delegate after voting"):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            poll_id=test_poll.id,
            start_date=datetime.utcnow(),
            end_date=None,
        )


@pytest.mark.asyncio
async def test_delegation_chain_depth(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)
    # Create a chain of users
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
        await db_session.refresh(u)
        users.append(u)

    # Create delegations in a chain
    for i in range(len(users) - 1):
        await service.create_delegation(
            delegator_id=users[i].id,
            delegatee_id=users[i + 1].id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        )

    # Try to create delegation that would exceed depth limit
    with pytest.raises(DelegationError, match="Delegation chain depth limit exceeded"):
        await service.create_delegation(
            delegator_id=users[-1].id,
            delegatee_id=users[0].id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_delegation_stats(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)

    # Create multiple users for delegations
    delegatees = [test_user2]
    for i in range(2):
        u = User(
            email=f"u{i}@example.com",
            username=f"u{i}",
            hashed_password=get_password_hash("pw"),
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        delegatees.append(u)

    # Create a unique poll for each delegation
    polls = []
    for i in range(len(delegatees)):
        poll = Poll(title=f"Poll {i}", description="desc", created_by=test_user.id)
        db_session.add(poll)
        await db_session.commit()
        await db_session.refresh(poll)
        polls.append(poll)

    # Create delegations to different users and polls
    for delegatee, poll in zip(delegatees, polls):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=delegatee.id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=poll.id,
        )

    # Get stats
    stats = await service.get_delegation_stats(test_user.id)
    assert stats["total_delegations"] == len(delegatees)
    assert stats["active_delegations"] == len(delegatees)
    assert stats["poll_specific_delegations"] == len(polls)
    assert stats["global_delegations"] == 0


@pytest.mark.asyncio
async def test_resolve_delegation_chain(db_session, test_user, test_user2, test_poll):
    service = DelegationService(db_session)
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        poll_id=test_poll.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    final_delegatee = await service.resolve_delegation_chain(test_user.id, test_poll.id)
    assert final_delegatee == test_user2.id


@pytest.mark.asyncio
async def test_delegation_chain_depth_limit(
    db_session, test_user, test_user2, test_user3
):
    service = DelegationService(db_session)
    # Create a poll
    poll = Poll(
        title="Test Poll",
        description="Test Description",
        created_by=test_user.id,
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create a chain: user1 -> user2 -> user3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=poll.id,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=poll.id,
    )

    # Test chain resolution
    final_delegatee = await service.resolve_delegation_chain(test_user.id, poll.id)
    assert final_delegatee == test_user3.id


@pytest.mark.asyncio
async def test_get_active_delegations(db_session, test_user, test_user2):
    service = DelegationService(db_session)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 1
    assert active_delegations[0].id == delegation.id


@pytest.mark.asyncio
async def test_revoke_nonexistent_delegation(db_session):
    service = DelegationService(db_session)
    with pytest.raises(DelegationNotFoundError):
        await service.revoke_delegation(uuid4())


@pytest.mark.asyncio
async def test_revoke_already_revoked_delegation(db_session, test_user, test_user2):
    service = DelegationService(db_session)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    await service.revoke_delegation(delegation.id)
    # Second revocation should succeed (idempotent)
    await service.revoke_delegation(delegation.id)
    active_delegation = await service.get_active_delegation(test_user.id)
    assert active_delegation is None


@pytest.mark.asyncio
async def test_circular_delegation_complex_chain(
    db_session, test_user, test_user2, test_user3
):
    service = DelegationService(db_session)
    # Create chain: user1 -> user2 -> user3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    # Try to create circular delegation: user3 -> user1
    with pytest.raises(CircularDelegationError):
        await service.create_delegation(
            delegator_id=test_user3.id,
            delegatee_id=test_user.id,
            start_date=datetime.utcnow(),
            end_date=None,
        )


@pytest.mark.asyncio
async def test_delegation_with_expired_end_date(db_session, test_user, test_user2):
    service = DelegationService(db_session)
    start_date = datetime.utcnow() - timedelta(days=2)  # 2 days ago
    end_date = datetime.utcnow() - timedelta(days=1)  # 1 day ago
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=start_date,
        end_date=end_date,
    )
    active_delegation = await service.get_active_delegation(test_user.id)
    assert active_delegation is None


@pytest.mark.asyncio
async def test_delegation_with_future_start_date(db_session, test_user, test_user2):
    service = DelegationService(db_session)
    future_date = datetime.utcnow() + timedelta(days=1)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=future_date,
        end_date=None,
    )
    active_delegation = await service.get_active_delegation(test_user.id)
    assert (
        active_delegation is None
    ), "Delegation with future start date should not be active"


@pytest.mark.asyncio
async def test_delegate_to_chain_member(db_session, test_user, test_user2, test_user3):
    service = DelegationService(db_session)
    # Create chain: user1 -> user2 -> user3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    # Try to delegate to user2 (already in chain)
    with pytest.raises(DelegationAlreadyExistsError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=datetime.utcnow(),
            end_date=None,
        )


@pytest.mark.asyncio
async def test_delegation_blocks_vote(db_session, test_user, test_user2, test_poll):
    service = DelegationService(db_session)
    # Create delegation
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        poll_id=test_poll.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    # Try to vote
    with pytest.raises(
        ValueError, match="Cannot vote while having an active delegation"
    ):
        await service.check_voting_allowed(test_user.id, test_poll.id)


@pytest.mark.asyncio
async def test_revocation_restores_voting_rights(
    db_session, test_user, test_user2, test_poll
):
    service = DelegationService(db_session)
    # Create delegation
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        poll_id=test_poll.id,
        start_date=datetime.utcnow(),
        end_date=None,
    )
    # Revoke delegation
    await service.revoke_delegation(delegation.id)
    # Check if voting is allowed
    assert await service.check_voting_allowed(test_user.id, test_poll.id)


@pytest.mark.asyncio
async def test_delegation_limit(db_session: AsyncSession, test_user: User):
    service = DelegationService(db_session)
    # Create 5 users to delegate to
    delegatees = []
    for i in range(5):
        u = User(
            email=f"u{i}@example.com",
            username=f"u{i}",
            hashed_password=get_password_hash("pw"),
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        delegatees.append(u)

    # Create 5 delegations (should succeed)
    for delegatee in delegatees:
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=delegatee.id,
            start_date=datetime.utcnow(),
            end_date=None,
        )

    # Try to create 6th delegation (should fail)
    with pytest.raises(Exception):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=delegatees[0].id,
            start_date=datetime.utcnow(),
            end_date=None,
        )


@pytest.mark.asyncio
async def test_delegation_stats_caching(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)

    # Create a poll
    poll = Poll(title="Test Poll", description="desc", created_by=test_user.id)
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create delegation
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=poll.id,
    )

    # Get stats twice - second call should use cache
    stats1 = await service.get_delegation_stats(poll_id=poll.id)
    stats2 = await service.get_delegation_stats(poll_id=poll.id)

    assert stats1 == stats2  # Should be identical due to caching
    assert stats1["active_delegations"] == 1
    assert any(d["user_id"] == str(test_user2.id) for d in stats1["top_delegatees"])


@pytest.mark.asyncio
async def test_delegation_chain_path(
    db_session: AsyncSession, test_user: User, test_user2: User, test_user3: User
):
    service = DelegationService(db_session)

    # Create a poll
    poll = Poll(title="Test Poll", description="desc", created_by=test_user.id)
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Create chain: user1 -> user2 -> user3
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=poll.id,
    )
    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=poll.id,
    )

    # Get chain with path
    final_delegatee, path = await service.resolve_delegation_chain(
        test_user.id, poll.id, include_path=True
    )

    assert final_delegatee == test_user3.id
    assert len(path) == 3
    assert path[0] == test_user.id
    assert path[1] == test_user2.id
    assert path[2] == test_user3.id


@pytest.mark.asyncio
async def test_concurrent_delegation_creation(
    db_session_factory, test_user: User, test_user2: User
):
    async def create_delegation():
        async with db_session_factory() as session:
            service = DelegationService(session)
            try:
                return await service.create_delegation(
                    delegator_id=test_user.id,
                    delegatee_id=test_user2.id,
                    start_date=datetime.utcnow(),
                    end_date=None,
                    poll_id=None,
                )
            except DelegationAlreadyExistsError:
                return None

    # Create two concurrent delegations
    tasks = [create_delegation(), create_delegation()]
    results = await asyncio.gather(*tasks)
    successes = [r for r in results if r is not None]
    failures = [r for r in results if r is None]
    assert len(successes) == 1
    assert len(failures) == 1


@pytest.mark.asyncio
async def test_overlapping_delegation_periods(
    db_session: AsyncSession, test_user: User, test_user2: User, test_user3: User
):
    """Test handling of delegations with overlapping time periods."""
    # Ensure users have unique emails
    test_user.email = f"{uuid4()}@example.com"
    test_user2.email = f"{uuid4()}@example.com"
    test_user3.email = f"{uuid4()}@example.com"
    db_session.add_all([test_user, test_user2, test_user3])
    await db_session.commit()
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
    # Try to create overlapping delegation
    with pytest.raises(DelegationAlreadyExistsError):
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user3.id,
            start_date=now + timedelta(days=15),  # Overlaps with first delegation
            end_date=now + timedelta(days=45),
            poll_id=None,
        )


@pytest.mark.asyncio
async def test_invalid_delegation_dates(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    service = DelegationService(db_session)

    # Test end date before start date
    with pytest.raises(InvalidDelegationPeriodError) as exc_info:
        await service.create_delegation(
            delegator_id=test_user.id,
            delegatee_id=test_user2.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() - timedelta(days=1),
            poll_id=None,
        )
    assert "End date must be after start date" in str(exc_info.value)


@pytest.mark.asyncio
async def test_multiple_active_chains(
    db_session: AsyncSession,
    test_user: User,
    test_user2: User,
    test_user3: User,
    test_user4: User,
):
    service = DelegationService(db_session)

    # Create two separate delegation chains
    # Chain 1: test_user -> test_user2 -> test_user3
    delegation1 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    delegation2 = await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    # Chain 2: test_user -> test_user4
    delegation3 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user4.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    # Verify both chains are active
    chain1_final = await service.resolve_delegation_chain(test_user.id, None)
    assert chain1_final[0] == test_user3.id

    chain2_final = await service.resolve_delegation_chain(test_user.id, None)
    assert (
        chain2_final[0] == test_user3.id
    )  # Should still resolve to test_user3 since it's the most recent chain

    # Create a new delegation from test_user4 to test_user3
    delegation4 = await service.create_delegation(
        delegator_id=test_user4.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    # Verify the final delegatee is still test_user3
    final_delegatee = await service.resolve_delegation_chain(test_user.id, None)
    assert final_delegatee[0] == test_user3.id


@pytest.mark.asyncio
async def test_revoked_intermediate_delegatee(
    db_session: AsyncSession, test_user: User, test_user2: User, test_user3: User
):
    """Test handling of delegation chain with revoked intermediate delegatee."""
    service = DelegationService(db_session)

    # Create a chain: user1 -> user2 -> user3
    delegation1 = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    delegation2 = await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )

    # Revoke the intermediate delegation
    await service.revoke_delegation(delegation1.id)

    # Verify the chain is broken
    final_delegatee = await service.resolve_delegation_chain(test_user.id, None)
    assert final_delegatee == test_user.id  # Should return to original delegator


@pytest.mark.asyncio
async def test_delegation_with_past_end_date(
    db_session: AsyncSession, test_user: User, test_user2: User
):
    """Test handling of delegation with end date in the past."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create delegation with end date in the past
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now - timedelta(days=2),
        end_date=now - timedelta(days=1),
        poll_id=None,
    )

    # Verify delegation is not active
    active_delegations = await service.get_active_delegations(test_user.id)
    assert len(active_delegations) == 0


@pytest.mark.asyncio
async def test_delegation_chain_with_expired_delegations(
    db_session: AsyncSession, test_user: User, test_user2: User, test_user3: User
):
    """Test handling of delegation chain with expired delegations."""
    service = DelegationService(db_session)
    now = datetime.utcnow()

    # Create a chain with an expired delegation in the middle
    await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=now - timedelta(days=2),
        end_date=now - timedelta(days=1),  # Expired
        poll_id=None,
    )

    await service.create_delegation(
        delegator_id=test_user2.id,
        delegatee_id=test_user3.id,
        start_date=now,
        end_date=None,
        poll_id=None,
    )

    # Verify the chain is broken at the expired delegation
    final_delegatee = await service.resolve_delegation_chain(test_user.id, None)
    assert final_delegatee == test_user.id  # Should return to original delegator
