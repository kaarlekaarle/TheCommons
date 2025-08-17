"""
Tests for runtime delegation warnings.

Tests the concentration monitor and super-delegate detector services
to ensure warnings are triggered correctly based on thresholds.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.concentration_monitor import ConcentrationMonitorService
from backend.services.super_delegate_detector import SuperDelegateDetectorService
from backend.models.delegation import Delegation, DelegationMode
from backend.models.user import User
from backend.models.field import Field


@pytest.mark.asyncio
async def test_concentration_warning_on_high_delegations(db_session: AsyncSession):
    """Test that concentration warnings are triggered when a delegatee has many delegations."""
    # Create test users
    delegatee_id = uuid4()
    delegator_ids = [uuid4() for _ in range(20)]  # 20 delegators
    
    # Create many delegations to the same delegatee
    for delegator_id in delegator_ids:
        delegation = Delegation(
            id=uuid4(),
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    # Create a few other delegations to different delegatees
    other_delegatee = uuid4()
    for i in range(5):
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=other_delegatee,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Test concentration monitor
    monitor = ConcentrationMonitorService(db_session)
    is_high, level, percent = await monitor.is_high_concentration(delegatee_id)
    
    # Should be high concentration (20/25 = 80%)
    assert is_high is True
    assert level == "high"
    assert percent == 0.8


@pytest.mark.asyncio
async def test_super_delegate_risk_on_many_fields(db_session: AsyncSession):
    """Test that super-delegate warnings are triggered when a delegatee is delegated in many fields."""
    delegatee_id = uuid4()
    
    # Create delegations across many fields
    for i in range(15):  # More than the 12 field threshold
        field_id = uuid4()
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="field",
            field_id=field_id,
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Test super-delegate detector
    detector = SuperDelegateDetectorService(db_session)
    risk, reason, stats = await detector.would_create_super_delegate(delegatee_id)
    
    # Should detect super-delegate risk due to many fields
    assert risk is True
    assert "distinct fields" in reason
    assert stats["projected_distinct_fields"] >= 12


@pytest.mark.asyncio
async def test_concentration_warning_in_api_response(db_session: AsyncSession, client, auth_headers):
    """Test that concentration warnings appear in API response."""
    # Create a delegatee with many delegations
    delegatee_id = uuid4()
    for i in range(15):
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Create delegation to the high-concentration delegatee
    response = await client.post(
        "/api/delegations",
        json={
            "delegatee_id": str(delegatee_id),
            "mode": "flexible_domain"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Should have warnings in response
    assert "warnings" in data
    assert "concentration" in data["warnings"]
    assert data["warnings"]["concentration"]["active"] is True


@pytest.mark.asyncio
async def test_super_delegate_risk_in_api_response(db_session: AsyncSession, client, auth_headers):
    """Test that super-delegate warnings appear in API response."""
    # Create a delegatee with many fields
    delegatee_id = uuid4()
    for i in range(15):
        field_id = uuid4()
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="field",
            field_id=field_id,
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Create delegation to the super-delegate
    response = await client.post(
        "/api/delegations",
        json={
            "delegatee_id": str(delegatee_id),
            "mode": "flexible_domain"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Should have warnings in response
    assert "warnings" in data
    assert "superDelegateRisk" in data["warnings"]
    assert data["warnings"]["superDelegateRisk"]["active"] is True


@pytest.mark.asyncio
async def test_no_warnings_for_normal_delegation(db_session: AsyncSession, client, auth_headers):
    """Test that no warnings are shown for normal delegation patterns."""
    # Create a delegatee with few delegations
    delegatee_id = uuid4()
    for i in range(3):  # Low number of delegations
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Create delegation to the normal delegatee
    response = await client.post(
        "/api/delegations",
        json={
            "delegatee_id": str(delegatee_id),
            "mode": "flexible_domain"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Should have warnings object but no active warnings
    assert "warnings" in data
    assert data["warnings"]["concentration"]["active"] is False
    assert data["warnings"]["superDelegateRisk"]["active"] is False


@pytest.mark.asyncio
async def test_warning_thresholds_are_respected(db_session: AsyncSession):
    """Test that warning thresholds are properly respected."""
    delegatee_id = uuid4()
    
    # Test concentration thresholds
    monitor = ConcentrationMonitorService(db_session)
    
    # Below warning threshold (8%)
    for i in range(5):
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    is_high, level, percent = await monitor.is_high_concentration(delegatee_id)
    assert is_high is False
    assert level == ""
    
    # Add more delegations to trigger warning
    for i in range(10):
        delegation = Delegation(
            id=uuid4(),
            delegator_id=uuid4(),
            delegatee_id=delegatee_id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            target_type="user",
            is_active=True
        )
        db_session.add(delegation)
    
    await db_session.commit()
    
    is_high, level, percent = await monitor.is_high_concentration(delegatee_id)
    assert is_high is True
    assert level in ["warn", "high"]
