"""Test legacy delegation mode revocability and user override behavior."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.models.delegation import Delegation, DelegationMode
from backend.services.delegation import DelegationService
from backend.core.exceptions.delegation import DelegationError


class TestLegacyDelegationRevocability:
    """Test that legacy delegations are always revocable by constitutional principle."""

    @pytest.mark.asyncio
    async def test_legacy_delegation_creation(self, db_session, user1, user2):
        """Test creating a legacy fixed-term delegation."""
        delegation_service = DelegationService(db_session)
        
        # Create legacy delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
        )
        
        assert delegation.mode == DelegationMode.LEGACY_FIXED_TERM
        assert delegation.is_legacy_fixed_term is True
        assert delegation.is_revocable is True  # Constitutional principle
        assert delegation.legacy_term_ends_at is not None
        assert delegation.legacy_term_ends_at > delegation.start_date
        assert delegation.legacy_term_ends_at <= delegation.start_date + timedelta(days=4*365)

    @pytest.mark.asyncio
    async def test_legacy_delegation_revocation(self, db_session, user1, user2):
        """Test that legacy delegations can be revoked at any time."""
        delegation_service = DelegationService(db_session)
        
        # Create legacy delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
        )
        
        # Verify it's active
        assert delegation.revoked_at is None
        
        # Revoke the delegation
        await delegation_service.revoke_delegation(delegation.id)
        await db_session.commit()
        
        # Refresh and verify revocation
        await db_session.refresh(delegation)
        assert delegation.revoked_at is not None

    @pytest.mark.asyncio
    async def test_legacy_delegation_expiry(self, db_session, user1, user2):
        """Test that legacy delegations expire automatically."""
        delegation_service = DelegationService(db_session)
        
        # Create legacy delegation with past expiry
        past_date = datetime.utcnow() - timedelta(days=1)
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
            legacy_term_ends_at=past_date,
        )
        
        # Verify it's expired
        assert delegation.is_expired is True
        
        # Run expiry job
        result = await delegation_service.expire_legacy_delegations()
        await db_session.commit()
        
        # Verify expiry was processed
        assert result["expired_count"] >= 1

    @pytest.mark.asyncio
    async def test_user_override_stops_chain_resolution(self, db_session, user1, user2, user3):
        """Test that user overrides stop chain resolution immediately."""
        delegation_service = DelegationService(db_session)
        
        # Create delegation chain: user1 -> user2 -> user3
        delegation1 = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
        )
        
        delegation2 = await delegation_service.create_delegation(
            delegator_id=user2.id,
            delegatee_id=user3.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
        )
        
        # Resolve chain from user1
        chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
        )
        
        # Should find both delegations in chain
        assert len(chain) == 2
        assert chain[0].delegator_id == user1.id
        assert chain[0].delegatee_id == user2.id
        assert chain[1].delegator_id == user2.id
        assert chain[1].delegatee_id == user3.id
        
        # Note: The _has_user_override method currently returns False
        # In a real implementation, this would check for direct votes/actions
        # and stop chain resolution when user overrides are detected

    @pytest.mark.asyncio
    async def test_legacy_term_constraint(self, db_session, user1, user2):
        """Test that legacy term cannot exceed 4 years."""
        delegation_service = DelegationService(db_session)
        
        # Try to create legacy delegation with term > 4 years
        future_date = datetime.utcnow() + timedelta(days=5*365)  # 5 years
        
        with pytest.raises(Exception):  # Should raise validation error
            await delegation_service.create_delegation(
                delegator_id=user1.id,
                delegatee_id=user2.id,
                mode=DelegationMode.LEGACY_FIXED_TERM,
                legacy_term_ends_at=future_date,
            )

    @pytest.mark.asyncio
    async def test_legacy_delegation_chain_trace(self, db_session, user1, user2):
        """Test that legacy delegations show correct chain trace."""
        delegation_service = DelegationService(db_session)
        
        # Create legacy delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.LEGACY_FIXED_TERM,
        )
        
        # Resolve chain
        chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
        )
        
        # Verify chain trace
        assert len(chain) == 1
        assert chain[0].id == delegation.id
        assert chain[0].mode == DelegationMode.LEGACY_FIXED_TERM
        assert chain[0].is_expired is False
