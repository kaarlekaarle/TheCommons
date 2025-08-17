"""Tests for transparency endpoints.

Tests that verify delegation chain visibility and inbound delegation patterns.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.delegation import Delegation, DelegationMode
from backend.models.user import User
from backend.models.field import Field
from backend.api.delegations import (
    get_my_delegation_chain,
    get_delegatee_inbound_delegations,
    get_delegation_health_summary
)


@pytest.mark.asyncio
async def test_get_my_delegation_chain(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that user's delegation chain is correctly returned."""
    # Create test users
    user1 = test_users[0]
    user2 = test_users[1]
    user3 = test_users[2]
    
    # Create a field
    field = Field(
        id=uuid4(),
        slug="test-field",
        label="Test Field",
        description="A test field for delegation",
        created_at=datetime.utcnow()
    )
    db_session.add(field)
    await db_session.commit()
    
    # Create delegations: user1 -> user2 -> user3 (in field)
    delegation1 = Delegation(
        delegator_id=user1.id,
        delegatee_id=user2.id,
        field_id=field.id,
        mode=DelegationMode.FLEXIBLE_DOMAIN,
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db_session.add(delegation1)
    
    # Create global delegation: user1 -> user3
    delegation2 = Delegation(
        delegator_id=user1.id,
        delegatee_id=user3.id,
        field_id=None,  # Global delegation
        mode=DelegationMode.LEGACY_FIXED_TERM,
        start_date=datetime.utcnow(),
        legacy_term_ends_at=datetime.utcnow() + timedelta(days=4*365),
        created_at=datetime.utcnow()
    )
    db_session.add(delegation2)
    
    await db_session.commit()
    
    # Test the endpoint
    from unittest.mock import AsyncMock
    mock_request = AsyncMock()
    
    # Mock the current user
    from backend.core.auth import get_current_active_user
    with pytest.MonkeyPatch().context() as m:
        m.setattr("backend.api.delegations.get_current_active_user", lambda: user1)
        
        result = await get_my_delegation_chain(
            current_user=user1,
            db=db_session
        )
    
    # Verify response structure
    assert "chains" in result
    assert "totalChains" in result
    assert result["totalChains"] == 2  # One field-specific, one global
    
    # Find the field-specific chain
    field_chain = None
    global_chain = None
    for chain in result["chains"]:
        if chain["fieldId"] == str(field.id):
            field_chain = chain
        elif chain["fieldId"] is None:
            global_chain = chain
    
    # Verify field-specific chain
    assert field_chain is not None
    assert len(field_chain["path"]) == 1
    assert field_chain["path"][0]["delegator"] == str(user1.id)
    assert field_chain["path"][0]["delegatee"] == str(user2.id)
    assert field_chain["path"][0]["mode"] == DelegationMode.FLEXIBLE_DOMAIN
    
    # Verify global chain
    assert global_chain is not None
    assert len(global_chain["path"]) == 1
    assert global_chain["path"][0]["delegator"] == str(user1.id)
    assert global_chain["path"][0]["delegatee"] == str(user3.id)
    assert global_chain["path"][0]["mode"] == DelegationMode.LEGACY_FIXED_TERM


@pytest.mark.asyncio
async def test_get_delegatee_inbound_delegations(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that inbound delegations to a delegatee are correctly returned."""
    # Create test users
    user1 = test_users[0]
    user2 = test_users[1]
    user3 = test_users[2]
    target_delegatee = test_users[3]
    
    # Create a field
    field = Field(
        id=uuid4(),
        slug="test-field",
        label="Test Field",
        description="A test field for delegation",
        created_at=datetime.utcnow()
    )
    db_session.add(field)
    await db_session.commit()
    
    # Create multiple delegations to the target delegatee
    delegations = []
    
    # user1 -> target_delegatee (field-specific)
    delegation1 = Delegation(
        delegator_id=user1.id,
        delegatee_id=target_delegatee.id,
        field_id=field.id,
        mode=DelegationMode.FLEXIBLE_DOMAIN,
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    delegations.append(delegation1)
    
    # user2 -> target_delegatee (global)
    delegation2 = Delegation(
        delegator_id=user2.id,
        delegatee_id=target_delegatee.id,
        field_id=None,
        mode=DelegationMode.LEGACY_FIXED_TERM,
        start_date=datetime.utcnow(),
        legacy_term_ends_at=datetime.utcnow() + timedelta(days=4*365),
        created_at=datetime.utcnow()
    )
    delegations.append(delegation2)
    
    # user3 -> target_delegatee (same field)
    delegation3 = Delegation(
        delegator_id=user3.id,
        delegatee_id=target_delegatee.id,
        field_id=field.id,
        mode=DelegationMode.FLEXIBLE_DOMAIN,
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    delegations.append(delegation3)
    
    for delegation in delegations:
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Test the endpoint without field filter
    from unittest.mock import AsyncMock
    mock_request = AsyncMock()
    
    # Mock the current user
    from backend.core.auth import get_current_active_user
    with pytest.MonkeyPatch().context() as m:
        m.setattr("backend.api.delegations.get_current_active_user", lambda: user1)
        
        result = await get_delegatee_inbound_delegations(
            delegatee_id=target_delegatee.id,
            field_id=None,
            limit=50,
            current_user=user1,
            db=db_session
        )
    
    # Verify response structure
    assert "delegateeId" in result
    assert "delegateeName" in result
    assert "inbound" in result
    assert "counts" in result
    
    assert result["delegateeId"] == str(target_delegatee.id)
    assert result["delegateeName"] == target_delegatee.username
    assert len(result["inbound"]) == 3
    assert result["counts"]["total"] == 3
    
    # Verify field counts
    field_counts = result["counts"]["byField"]
    assert field_counts["global"] == 1  # user2's global delegation
    assert field_counts[str(field.id)] == 2  # user1 and user3's field delegations
    
    # Test with field filter
    result_filtered = await get_delegatee_inbound_delegations(
        delegatee_id=target_delegatee.id,
        field_id=field.id,
        limit=50,
        current_user=user1,
        db=db_session
    )
    
    assert len(result_filtered["inbound"]) == 2  # Only field-specific delegations
    assert result_filtered["counts"]["total"] == 2


@pytest.mark.asyncio
async def test_get_delegation_health_summary(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that delegation health summary is correctly returned."""
    # Create test users
    user1 = test_users[0]
    user2 = test_users[1]
    user3 = test_users[2]
    
    # Create fields
    field1 = Field(
        id=uuid4(),
        slug="field-1",
        label="Field 1",
        description="First test field",
        created_at=datetime.utcnow()
    )
    field2 = Field(
        id=uuid4(),
        slug="field-2", 
        label="Field 2",
        description="Second test field",
        created_at=datetime.utcnow()
    )
    db_session.add(field1)
    db_session.add(field2)
    await db_session.commit()
    
    # Create delegations to make user1 the top delegatee
    delegations = []
    
    # Multiple delegations to user1 (should be top delegatee)
    for i in range(5):
        delegator = test_users[i + 3] if i + 3 < len(test_users) else test_users[3]
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=user1.id,
            field_id=field1.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            start_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        delegations.append(delegation)
    
    # Some delegations to user2
    for i in range(3):
        delegator = test_users[i + 8] if i + 8 < len(test_users) else test_users[4]
        delegation = Delegation(
            delegator_id=delegator.id,
            delegatee_id=user2.id,
            field_id=field2.id,
            mode=DelegationMode.FLEXIBLE_DOMAIN,
            start_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        delegations.append(delegation)
    
    # One delegation to user3
    delegation = Delegation(
        delegator_id=test_users[-1] if len(test_users) > 5 else test_users[5],
        delegatee_id=user3.id,
        field_id=field1.id,
        mode=DelegationMode.FLEXIBLE_DOMAIN,
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    delegations.append(delegation)
    
    for delegation in delegations:
        db_session.add(delegation)
    
    await db_session.commit()
    
    # Test the endpoint
    from unittest.mock import AsyncMock
    mock_request = AsyncMock()
    
    # Mock the current user
    from backend.core.auth import get_current_active_user
    with pytest.MonkeyPatch().context() as m:
        m.setattr("backend.api.delegations.get_current_active_user", lambda: user1)
        
        result = await get_delegation_health_summary(
            limit=10,
            current_user=user1,
            db=db_session
        )
    
    # Verify response structure
    assert "topDelegatees" in result
    assert "byField" in result
    assert "totalDelegations" in result
    assert "generatedAt" in result
    
    assert result["totalDelegations"] == 9  # 5 + 3 + 1
    
    # Verify top delegatees
    top_delegatees = result["topDelegatees"]
    assert len(top_delegatees) >= 1
    
    # user1 should be the top delegatee
    top_delegatee = top_delegatees[0]
    assert top_delegatee["id"] == str(user1.id)
    assert top_delegatee["name"] == user1.username
    assert top_delegatee["count"] == 5
    assert top_delegatee["percent"] == pytest.approx(55.56, abs=0.01)  # 5/9 * 100
    
    # Verify by field data
    by_field = result["byField"]
    assert str(field1.id) in by_field
    assert str(field2.id) in by_field
    
    # Check field1 data
    field1_data = by_field[str(field1.id)]
    assert len(field1_data) >= 2  # user1 and user3
    
    # user1 should be top in field1
    field1_top = field1_data[0]
    assert field1_top["id"] == str(user1.id)
    assert field1_top["count"] == 5


@pytest.mark.asyncio
async def test_transparency_endpoints_privacy_respect(
    db_session: AsyncSession, 
    test_users: list[User]
):
    """Test that transparency endpoints respect privacy rules."""
    # Create test users
    user1 = test_users[0]
    user2 = test_users[1]
    
    # Create a delegation
    delegation = Delegation(
        delegator_id=user1.id,
        delegatee_id=user2.id,
        field_id=None,
        mode=DelegationMode.FLEXIBLE_DOMAIN,
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db_session.add(delegation)
    await db_session.commit()
    
    # Test that only usernames are exposed (no email, etc.)
    from unittest.mock import AsyncMock
    mock_request = AsyncMock()
    
    # Mock the current user
    from backend.core.auth import get_current_active_user
    with pytest.MonkeyPatch().context() as m:
        m.setattr("backend.api.delegations.get_current_active_user", lambda: user1)
        
        # Test inbound endpoint
        result = await get_delegatee_inbound_delegations(
            delegatee_id=user2.id,
            field_id=None,
            limit=50,
            current_user=user1,
            db=db_session
        )
    
    # Verify only username is exposed, not email
    inbound_item = result["inbound"][0]
    assert "delegatorName" in inbound_item
    assert "delegatorId" in inbound_item
    assert "email" not in inbound_item  # Privacy check
    
    # Test health summary endpoint
    result = await get_delegation_health_summary(
        limit=10,
        current_user=user1,
        db=db_session
    )
    
    # Verify only username is exposed
    top_delegatee = result["topDelegatees"][0]
    assert "name" in top_delegatee
    assert "email" not in top_delegatee  # Privacy check
