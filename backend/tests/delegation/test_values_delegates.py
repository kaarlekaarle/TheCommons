"""Tests for Values-as-Delegates & Unified Ledger constitutional guardrails.

Tests that people, values, and ideas are equally supported as delegation targets.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.label import Label
from backend.services.delegation import DelegationService
from backend.core.exceptions.delegation import DelegationNotFoundError


@pytest.mark.asyncio
async def test_delegate_to_person(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test delegation to a person (existing functionality)."""
    # Create delegation to user
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
    
    # Test chain resolution
    chain = await service.resolve_delegation_chain(test_user.id)
    assert len(chain) == 2
    assert chain == [str(test_user.id), str(test_user2.id)]


@pytest.mark.asyncio
async def test_delegate_to_value(db_session: AsyncSession, test_user: User):
    """Test delegation to a value/principle entity."""
    # TODO: Implement backend support for value-based delegation
    # TODO: Create Value entity model
    # TODO: Add value_id field to delegation model
    # TODO: Implement value-based voting resolution
    
    # Placeholder test that will fail until implemented
    assert False, "TODO: Implement delegation to value/principle entities"


@pytest.mark.asyncio
async def test_delegate_to_idea(db_session: AsyncSession, test_user: User):
    """Test delegation to an idea/proposal entity."""
    # TODO: Implement backend support for idea-based delegation
    # TODO: Create Idea entity model
    # TODO: Add idea_id field to delegation model
    # TODO: Implement idea-based voting resolution
    
    # Placeholder test that will fail until implemented
    assert False, "TODO: Implement delegation to idea/proposal entities"


@pytest.mark.asyncio
async def test_single_table_for_all_types(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test that all delegation types use unified schema."""
    # TODO: Implement unified schema for all delegation types
    # TODO: Add type discriminator field to delegation model
    # TODO: Ensure person, value, and idea delegations use same table
    
    # Create delegation to person (existing functionality)
    service = DelegationService(db_session)
    person_delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    
    # TODO: Create delegation to value
    # TODO: Create delegation to idea
    # TODO: Verify all stored in same table with type discriminator
    # TODO: Test unified querying across types
    
    # Placeholder assertion
    assert person_delegation is not None, "Person delegation should work"
    assert False, "TODO: Implement unified schema for all delegation types"


@pytest.mark.asyncio
async def test_flow_resolves_across_types(db_session: AsyncSession, test_user: User, test_user2: User):
    """Test delegation resolution across different entity types."""
    # TODO: Implement cross-type delegation resolution
    # TODO: Support mixed delegation chains (person -> value -> person)
    # TODO: Implement proper type handling in chain resolution
    
    # Setup basic person-to-person delegation
    service = DelegationService(db_session)
    delegation = await service.create_delegation(
        delegator_id=test_user.id,
        delegatee_id=test_user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    
    # TODO: Add value delegation to chain
    # TODO: Test resolution across entity types
    # TODO: Verify proper type handling
    
    # Placeholder assertion
    assert delegation is not None, "Basic delegation should work"
    assert False, "TODO: Implement cross-type delegation resolution"
