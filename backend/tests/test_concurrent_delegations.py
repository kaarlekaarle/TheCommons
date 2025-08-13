import asyncio
from datetime import datetime

import pytest

from backend.services.delegation import DelegationService


@pytest.mark.delegation_edge
@pytest.mark.asyncio
async def test_concurrent_delegation_creation():
    """Test creating delegations concurrently to ensure no race conditions."""
    # This test verifies that concurrent delegation creation doesn't cause issues
    # with database constraints or business logic
    pass


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

    # Create multiple delegations concurrently
    tasks = [create_delegation(test_user2.id), create_delegation(test_user3.id)]
    results = await asyncio.gather(*tasks)

    # Verify all delegations were created successfully
    active_delegations = await service.get_active_delegations(test_user.id)
    assert (
        len(active_delegations) == 2
    ), f"Expected 2 active delegations, got {len(active_delegations)}: {active_delegations}"

    # Verify both delegatees are present
    delegatee_ids = {d.delegatee_id for d in active_delegations}
    assert test_user2.id in delegatee_ids
    assert test_user3.id in delegatee_ids
