"""Integration tests for delegation functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.services.delegation import DelegationService
from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    SelfDelegationError,
    InvalidDelegationPeriodError,
    DelegationLimitExceededError,
)
from backend.models.delegation import Delegation
from backend.models.user import User
from tests.utils import create_test_user

@pytest.fixture
async def test_users(db_session):
    """Create test users for delegation tests."""
    user1 = await create_test_user(db_session, email="user1@test.com")
    user2 = await create_test_user(db_session, email="user2@test.com")
    user3 = await create_test_user(db_session, email="user3@test.com")
    return user1, user2, user3

@pytest.fixture
async def delegation_service(db_session):
    """Create a delegation service instance."""
    return DelegationService(db_session)

@pytest.mark.asyncio
class TestDelegationCreation:
    """Test suite for delegation creation functionality."""

    async def test_basic_delegation_creation(self, delegation_service, test_users):
        """Test basic delegation creation between two users."""
        user1, user2, _ = test_users
        
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
            end_date=None,
        )
        
        assert delegation is not None
        assert delegation.delegator_id == user1.id
        assert delegation.delegatee_id == user2.id
        assert delegation.end_date is None
        assert delegation.is_active is True

    async def test_delegation_with_end_date(self, delegation_service, test_users):
        """Test delegation creation with an end date."""
        user1, user2, _ = test_users
        end_date = datetime.utcnow() + timedelta(days=30)
        
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
            end_date=end_date,
        )
        
        assert delegation.end_date == end_date
        assert delegation.is_active is True

    async def test_self_delegation_prevention(self, delegation_service, test_users):
        """Test that self-delegation is prevented."""
        user1, _, _ = test_users
        
        with pytest.raises(SelfDelegationError):
            await delegation_service.create_delegation(
                delegator_id=user1.id,
                delegatee_id=user1.id,
                start_date=datetime.utcnow(),
            )

    async def test_circular_delegation_prevention(self, delegation_service, test_users):
        """Test that circular delegations are prevented."""
        user1, user2, _ = test_users
        
        # Create first delegation
        await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        
        # Attempt to create circular delegation
        with pytest.raises(CircularDelegationError):
            await delegation_service.create_delegation(
                delegator_id=user2.id,
                delegatee_id=user1.id,
                start_date=datetime.utcnow(),
            )

    async def test_duplicate_delegation_prevention(self, delegation_service, test_users):
        """Test that duplicate delegations are prevented."""
        user1, user2, _ = test_users
        
        # Create first delegation
        await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        
        # Attempt to create duplicate delegation
        with pytest.raises(DelegationAlreadyExistsError):
            await delegation_service.create_delegation(
                delegator_id=user1.id,
                delegatee_id=user2.id,
                start_date=datetime.utcnow(),
            )

    async def test_invalid_delegation_period(self, delegation_service, test_users):
        """Test that invalid delegation periods are rejected."""
        user1, user2, _ = test_users
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)  # End date before start date
        
        with pytest.raises(InvalidDelegationPeriodError):
            await delegation_service.create_delegation(
                delegator_id=user1.id,
                delegatee_id=user2.id,
                start_date=start_date,
                end_date=end_date,
            )

@pytest.mark.asyncio
class TestDelegationQueries:
    """Test suite for delegation query functionality."""

    async def test_get_active_delegations(self, delegation_service, test_users):
        """Test retrieving active delegations."""
        user1, user2, user3 = test_users
        
        # Create multiple delegations
        await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user3.id,
            start_date=datetime.utcnow(),
        )
        
        # Get active delegations
        active_delegations = await delegation_service.get_active_delegations(user1.id)
        assert len(active_delegations) == 2
        assert all(d.is_active for d in active_delegations)

    async def test_get_delegation_chain(self, delegation_service, test_users):
        """Test retrieving delegation chain."""
        user1, user2, user3 = test_users
        
        # Create delegation chain
        await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        await delegation_service.create_delegation(
            delegator_id=user2.id,
            delegatee_id=user3.id,
            start_date=datetime.utcnow(),
        )
        
        # Get delegation chain
        chain = await delegation_service.get_delegation_chain(user1.id)
        assert len(chain) == 2
        assert chain[0].delegatee_id == user2.id
        assert chain[1].delegatee_id == user3.id

@pytest.mark.asyncio
class TestDelegationUpdates:
    """Test suite for delegation update functionality."""

    async def test_update_delegation_end_date(self, delegation_service, test_users):
        """Test updating delegation end date."""
        user1, user2, _ = test_users
        
        # Create delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        
        # Update end date
        new_end_date = datetime.utcnow() + timedelta(days=30)
        updated = await delegation_service.update_delegation(
            delegation_id=delegation.id,
            end_date=new_end_date,
        )
        
        assert updated.end_date == new_end_date
        assert updated.is_active is True

    async def test_deactivate_delegation(self, delegation_service, test_users):
        """Test deactivating a delegation."""
        user1, user2, _ = test_users
        
        # Create delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
        )
        
        # Deactivate delegation
        updated = await delegation_service.update_delegation(
            delegation_id=delegation.id,
            is_active=False,
        )
        
        assert updated.is_active is False 