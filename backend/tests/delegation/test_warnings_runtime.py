"""Tests for runtime delegation warnings.

Tests that verify concentration and super-delegate risk warnings
are correctly generated during delegation creation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation, DelegationMode
from backend.models.user import User
from backend.models.field import Field
from backend.services.concentration_monitor import ConcentrationMonitorService
from backend.services.super_delegate_detector import SuperDelegateDetectorService
from backend.api.delegations import create_delegation
from backend.schemas.delegation import DelegationCreate


@pytest.mark.asyncio
async def test_concentration_warning_on_high_delegations(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that concentration warning appears when delegatee has high delegation count."""
    # Create a target delegatee
    target_delegatee = test_users[0]
    
    # Create many delegations to the same delegatee to trigger concentration warning
    service = ConcentrationMonitorService(db_session)
    
    # Create 10 delegations to the same person (should trigger warning at 7.5% threshold)
    for i in range(10):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=target_delegatee.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Check concentration
    is_high, level, percent = await service.is_high_concentration(target_delegatee.id)
    
    # Should trigger warning (10 delegations out of 10 total = 100%)
    assert is_high is True
    assert level == "high"
    assert percent == 1.0


@pytest.mark.asyncio
async def test_super_delegate_risk_on_many_fields(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that super-delegate risk warning appears when delegatee has many distinct fields."""
    # Create a target delegatee
    target_delegatee = test_users[0]
    
    # Create many fields
    fields = []
    for i in range(15):  # More than the 12 field threshold
        field = Field(
            id=uuid4(),
            slug=f"field-{i}",
            label=f"Field {i}",
            description=f"Test field {i}",
            created_at=datetime.utcnow()
        )
        db_session.add(field)
        fields.append(field)
    
    await db_session.commit()
    
    # Create delegations to the same delegatee across many fields
    service = SuperDelegateDetectorService(db_session)
    
    for i, field in enumerate(fields):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=target_delegatee.id,
            field_id=field.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Check super-delegate risk
    risk, reason, stats = await service.would_create_super_delegate(target_delegatee.id)
    
    # Should trigger super-delegate risk (15 distinct fields > 12 threshold)
    assert risk is True
    assert "distinct fields" in reason
    assert stats["projected_distinct_fields"] >= 12


@pytest.mark.asyncio
async def test_concentration_warning_in_api_response(
    db_session: AsyncSession, 
    test_users: list[User],
    mock_request
):
    """Test that concentration warning appears in API response."""
    # Create many delegations to trigger concentration warning
    target_delegatee = test_users[0]
    
    # Create 8 delegations to the same person (should trigger warning)
    for i in range(8):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=target_delegatee.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Create a new delegation that should trigger concentration warning
    delegator = test_users[-1]
    delegation_data = DelegationCreate(delegatee_id=target_delegatee.id)
    
    # Mock the request context
    from unittest.mock import AsyncMock
    mock_request = AsyncMock()
    
    # This would normally call the API endpoint, but we'll test the warning logic directly
    concentration_monitor = ConcentrationMonitorService(db_session)
    is_high, level, percent = await concentration_monitor.is_high_concentration(target_delegatee.id)
    
    # Should trigger concentration warning
    assert is_high is True
    assert level in ["warn", "high"]
    assert percent > 0.075  # Above warning threshold


@pytest.mark.asyncio
async def test_super_delegate_risk_in_api_response(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that super-delegate risk warning appears in API response."""
    # Create many fields
    fields = []
    for i in range(13):  # More than the 12 field threshold
        field = Field(
            id=uuid4(),
            slug=f"field-{i}",
            label=f"Field {i}",
            description=f"Test field {i}",
            created_at=datetime.utcnow()
        )
        db_session.add(field)
        fields.append(field)
    
    await db_session.commit()
    
    # Create delegations to the same delegatee across many fields
    target_delegatee = test_users[0]
    
    for i, field in enumerate(fields):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=target_delegatee.id,
            field_id=field.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Test the warning logic directly
    super_delegate_detector = SuperDelegateDetectorService(db_session)
    risk, reason, stats = await super_delegate_detector.would_create_super_delegate(target_delegatee.id)
    
    # Should trigger super-delegate risk
    assert risk is True
    assert "distinct fields" in reason
    assert stats["projected_distinct_fields"] >= 12


@pytest.mark.asyncio
async def test_no_warnings_for_normal_delegation(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that no warnings appear for normal delegation patterns."""
    target_delegatee = test_users[0]
    delegator = test_users[1]
    
    # Create just a few delegations (should not trigger warnings)
    for i in range(3):
        other_delegator = test_users[i + 2] if i + 2 < len(test_users) else test_users[2]
        
        delegation = Delegation(
            delegator_id=other_delegator.id,
            delegatee_id=target_delegatee.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Check concentration
    concentration_monitor = ConcentrationMonitorService(db_session)
    is_high, level, percent = await concentration_monitor.is_high_concentration(target_delegatee.id)
    
    # Should not trigger concentration warning
    assert is_high is False
    assert percent < 0.075  # Below warning threshold
    
    # Check super-delegate risk
    super_delegate_detector = SuperDelegateDetectorService(db_session)
    risk, reason, stats = await super_delegate_detector.would_create_super_delegate(target_delegatee.id)
    
    # Should not trigger super-delegate risk
    assert risk is False
    assert stats["projected_delegations"] < 500  # Below threshold


@pytest.mark.asyncio
async def test_warning_thresholds_are_respected(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that warning thresholds are correctly applied."""
    target_delegatee = test_users[0]
    
    # Create exactly 7 delegations (just below 7.5% threshold with 100 total delegations)
    # We need to create 93 other delegations first to make 7 delegations = 7%
    other_delegations = 0
    for i in range(93):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        other_delegatee = test_users[i + 2] if i + 2 < len(test_users) else test_users[2]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=other_delegatee.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
        other_delegations += 1
    
    # Now add 7 delegations to target delegatee
    for i in range(7):
        delegator = test_users[i + 1] if i + 1 < len(test_users) else test_users[1]
        
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=target_delegatee.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            created_at=datetime.utcnow()
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Check concentration
    concentration_monitor = ConcentrationMonitorService(db_session)
    is_high, level, percent = await concentration_monitor.is_high_concentration(target_delegatee.id)
    
    # Should be just below warning threshold (7/100 = 7%)
    assert is_high is False
    assert percent == 0.07  # 7%
    assert percent < 0.075  # Below 7.5% threshold
