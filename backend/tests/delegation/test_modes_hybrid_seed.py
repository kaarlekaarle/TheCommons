"""Test hybrid seed delegation mode behavior."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.models.delegation import Delegation, DelegationMode
from backend.models.field import Field
from backend.services.delegation import DelegationService


class TestHybridSeedDelegation:
    """Test hybrid seed delegation: global fallback + per-field refinement."""

    @pytest.mark.asyncio
    async def test_hybrid_seed_creation(self, db_session, user1, user2):
        """Test creating a hybrid seed delegation."""
        delegation_service = DelegationService(db_session)
        
        # Create hybrid seed delegation (global fallback)
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
        )
        
        assert delegation.mode == DelegationMode.HYBRID_SEED
        assert delegation.is_legacy_fixed_term is False
        assert delegation.is_revocable is True
        assert delegation.legacy_term_ends_at is None

    @pytest.mark.asyncio
    async def test_hybrid_seed_with_field_override(self, db_session, user1, user2, user3):
        """Test that per-field delegation overrides hybrid seed."""
        delegation_service = DelegationService(db_session)
        
        # Create a field
        field = Field(
            slug="climate",
            name="Climate Policy",
            description="Climate and environmental policy",
        )
        db_session.add(field)
        await db_session.flush()
        
        # Create hybrid seed (global fallback)
        global_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
        )
        
        # Create field-specific delegation (should override global)
        field_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user3.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            field_id=field.id,
        )
        
        # Resolve chain for global context
        global_chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
        )
        
        # Should find global hybrid seed
        assert len(global_chain) == 1
        assert global_chain[0].delegatee_id == user2.id
        assert global_chain[0].mode == DelegationMode.HYBRID_SEED
        
        # Resolve chain for field context
        field_chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
            field_id=field.id,
        )
        
        # Should find field-specific delegation (overrides global)
        assert len(field_chain) == 1
        assert field_chain[0].delegatee_id == user3.id
        assert field_chain[0].mode == DelegationMode.FLEXIBLE_DOMAIN
        assert field_chain[0].field_id == field.id

    @pytest.mark.asyncio
    async def test_hybrid_seed_resolution_order(self, db_session, user1, user2, user3):
        """Test that hybrid seed delegations are resolved in correct order."""
        delegation_service = DelegationService(db_session)
        
        # Create hybrid seed delegation
        hybrid_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
        )
        
        # Create flexible domain delegation (should be lower priority)
        flexible_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user3.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
        )
        
        # Resolve chain
        chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
        )
        
        # Should find hybrid seed first (higher priority)
        assert len(chain) == 1
        assert chain[0].id == hybrid_delegation.id
        assert chain[0].mode == DelegationMode.HYBRID_SEED
        assert chain[0].delegatee_id == user2.id

    @pytest.mark.asyncio
    async def test_hybrid_seed_chain_trace(self, db_session, user1, user2):
        """Test that hybrid seed delegations show correct chain trace."""
        delegation_service = DelegationService(db_session)
        
        # Create hybrid seed delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
        )
        
        # Resolve chain
        chain = await delegation_service.resolve_delegation_chain(
            user_id=user1.id,
        )
        
        # Verify chain trace
        assert len(chain) == 1
        assert chain[0].id == delegation.id
        assert chain[0].mode == DelegationMode.HYBRID_SEED
        assert chain[0].target_type == "global"

    @pytest.mark.asyncio
    async def test_hybrid_seed_revocation(self, db_session, user1, user2):
        """Test that hybrid seed delegations can be revoked."""
        delegation_service = DelegationService(db_session)
        
        # Create hybrid seed delegation
        delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
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
    async def test_hybrid_seed_with_multiple_targets(self, db_session, user1, user2, user3):
        """Test hybrid seed with multiple target types."""
        delegation_service = DelegationService(db_session)
        
        # Create a field
        field = Field(
            slug="economy",
            name="Economic Policy",
            description="Economic and fiscal policy",
        )
        db_session.add(field)
        await db_session.flush()
        
        # Create hybrid seed (global)
        global_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user2.id,
            mode=DelegationMode.HYBRID_SEED,
        )
        
        # Create field-specific delegation
        field_delegation = await delegation_service.create_delegation(
            delegator_id=user1.id,
            delegatee_id=user3.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            field_id=field.id,
        )
        
        # Verify both delegations exist
        assert global_delegation.mode == DelegationMode.HYBRID_SEED
        assert field_delegation.mode == DelegationMode.FLEXIBLE_DOMAIN
        assert field_delegation.field_id == field.id
        
        # Verify target types
        assert global_delegation.target_type == "global"
        assert field_delegation.target_type == "field"
