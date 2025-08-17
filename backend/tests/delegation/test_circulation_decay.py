"""Tests for Circulation & Decay constitutional guardrails.

Tests that power must circulate, no permanents, and delegation decay mechanisms.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation
from backend.models.user import User
from backend.models.poll import Poll
from backend.services.delegation import DelegationService
from backend.core.exceptions.delegation import DelegationNotFoundError


@pytest.mark.asyncio
async def test_revocation_immediate_effect(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test that delegation revocation takes effect immediately."""
    # Setup delegation
    service = DelegationService(db_session)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    
    # Verify delegation is active
    active_delegation = await service.get_active_delegation(test_user.id)
    assert active_delegation is not None
    assert active_delegation.delegatee_id == test_user2.id
    
    # Revoke delegation
    await service.revoke_delegation(delegation.id)
    
    # Assert delegation is immediately inactive
    active_delegation = await service.get_active_delegation(test_user.id)
    assert active_delegation is None
    
    # Verify chain resolution returns original user
    chain = await service.resolve_delegation_chain(test_user.id)
    assert len(chain) == 1
    assert chain[0] == str(test_user.id)


@pytest.mark.asyncio
async def test_revocation_chain_break(db_session: AsyncSession, test_user: User, test_user2: User, test_user3: User):
    """Test that revocation breaks delegation chains."""
    # Setup chain: test_user -> test_user2 -> test_user3
    service = DelegationService(db_session)
    
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
    
    # Verify full chain exists
    chain = await service.resolve_delegation_chain(test_user.id)
    assert len(chain) == 3
    assert chain == [str(test_user.id), str(test_user2.id), str(test_user3.id)]
    
    # Revoke middle delegation (test_user2 -> test_user3)
    await service.revoke_delegation(delegation2.id)
    
    # Assert chain resolution stops at test_user2
    chain = await service.resolve_delegation_chain(test_user.id)
    assert len(chain) == 2
    assert chain == [str(test_user.id), str(test_user2.id)]
    
    # Verify no phantom votes from test_user3
    # TODO: Implement vote verification to ensure test_user3's votes don't count for test_user


@pytest.mark.asyncio
async def test_delegation_auto_expires(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test that delegations automatically expire based on end_date."""
    # Create delegation with end_date in past
    service = DelegationService(db_session)
    past_date = datetime.utcnow() - timedelta(hours=1)
    
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow() - timedelta(hours=2),
        end_date=past_date,
        poll_id=None,
    )
    
    # Assert delegation is not active
    active_delegation = await service.get_active_delegation(test_user.id)
    assert active_delegation is None
    
    # Verify chain resolution returns original user
    chain = await service.resolve_delegation_chain(test_user.id)
    assert len(chain) == 1
    assert chain[0] == str(test_user.id)


@pytest.mark.asyncio
async def test_dormant_reconfirmation_required(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test that dormant delegations require reconfirmation."""
    # TODO: Implement backend support for dormant delegation detection
    # TODO: Add dormant_reconfirmation_required field to delegation model
    # TODO: Create background job to mark old delegations as dormant
    # TODO: Implement reconfirmation API endpoint
    
    # Create delegation with old start_date
    service = DelegationService(db_session)
    old_date = datetime.utcnow() - timedelta(days=180)  # 6 months old
    
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=old_date,
        end_date=None,
        poll_id=None,
    )
    
    # TODO: Trigger dormant check
    # TODO: Assert reconfirmation is required
    # TODO: Verify delegation is marked as dormant
    
    # Placeholder assertion that will fail until implemented
    assert False, "TODO: Implement dormant reconfirmation mechanism"


@pytest.mark.asyncio
async def test_no_permanent_flag_in_schema(db_session: AsyncSession):
    """Test that no permanent delegation flags exist in schema."""
    # Inspect delegation model schema
    delegation_columns = Delegation.__table__.columns.keys()
    
    # Assert no permanent/is_permanent fields exist
    permanent_flags = [col for col in delegation_columns if 'permanent' in col.lower()]
    assert len(permanent_flags) == 0, f"Found permanent flags in schema: {permanent_flags}"
    
    # Verify all delegations have temporal controls
    temporal_fields = ['start_date', 'end_date', 'revoked_at', 'created_at', 'updated_at']
    for field in temporal_fields:
        assert field in delegation_columns, f"Missing temporal field: {field}"
    
    # Verify soft deletion is available
    assert 'is_deleted' in delegation_columns, "Missing soft deletion field"
    assert 'deleted_at' in delegation_columns, "Missing deletion timestamp field"
