"""
Tests for delegation stats provider contract.

These tests ensure that the delegation stats provider returns a complete,
consistent contract with all required keys and correct types, even when
there are zero delegations in the database.
"""

import pytest
from typing import Dict, Any, List, Tuple
from uuid import uuid4
from datetime import datetime

from backend.services.delegation import DelegationService
from backend.models.delegation import Delegation
from backend.models.user import User
from backend.core.security import get_password_hash


@pytest.mark.asyncio
async def test_delegation_stats_contract_empty_db(db_session):
    """Test that delegation stats provider returns complete contract with zero delegations."""
    service = DelegationService(db_session)
    
    # Test with no poll_id (global stats)
    stats = await service.get_delegation_stats(poll_id=None)
    
    # Verify all required keys exist
    required_keys = {
        "active_delegations",
        "unique_delegators", 
        "unique_delegatees",
        "avg_chain_length",
        "max_chain_length",
        "cycles_detected",
        "orphaned_delegations",
        "top_delegatees",
        "poll_id"
    }
    
    assert set(stats.keys()) == required_keys, f"Missing keys: {required_keys - set(stats.keys())}"
    
    # Verify correct types
    assert isinstance(stats["active_delegations"], int)
    assert isinstance(stats["unique_delegators"], int)
    assert isinstance(stats["unique_delegatees"], int)
    assert isinstance(stats["avg_chain_length"], float)
    assert isinstance(stats["max_chain_length"], int)
    assert isinstance(stats["cycles_detected"], int)
    assert isinstance(stats["orphaned_delegations"], int)
    assert isinstance(stats["top_delegatees"], list)
    assert stats["poll_id"] is None
    
    # Verify zero values for empty database
    assert stats["active_delegations"] == 0
    assert stats["unique_delegators"] == 0
    assert stats["unique_delegatees"] == 0
    assert stats["avg_chain_length"] == 0.0
    assert stats["max_chain_length"] == 0
    assert stats["cycles_detected"] == 0
    assert stats["orphaned_delegations"] == 0
    assert stats["top_delegatees"] == []


@pytest.mark.asyncio
async def test_delegation_stats_contract_with_poll_id(db_session):
    """Test that delegation stats provider returns complete contract with specific poll_id."""
    service = DelegationService(db_session)
    
    # Test with specific poll_id
    poll_id = uuid4()
    stats = await service.get_delegation_stats(poll_id=poll_id)
    
    # Verify all required keys exist
    required_keys = {
        "active_delegations",
        "unique_delegators", 
        "unique_delegatees",
        "avg_chain_length",
        "max_chain_length",
        "cycles_detected",
        "orphaned_delegations",
        "top_delegatees",
        "poll_id"
    }
    
    assert set(stats.keys()) == required_keys, f"Missing keys: {required_keys - set(stats.keys())}"
    
    # Verify correct types
    assert isinstance(stats["active_delegations"], int)
    assert isinstance(stats["unique_delegators"], int)
    assert isinstance(stats["unique_delegatees"], int)
    assert isinstance(stats["avg_chain_length"], float)
    assert isinstance(stats["max_chain_length"], int)
    assert isinstance(stats["cycles_detected"], int)
    assert isinstance(stats["orphaned_delegations"], int)
    assert isinstance(stats["top_delegatees"], list)
    assert isinstance(stats["poll_id"], str)
    assert stats["poll_id"] == str(poll_id)
    
    # Verify zero values for non-existent poll
    assert stats["active_delegations"] == 0
    assert stats["unique_delegators"] == 0
    assert stats["unique_delegatees"] == 0
    assert stats["avg_chain_length"] == 0.0
    assert stats["max_chain_length"] == 0
    assert stats["cycles_detected"] == 0
    assert stats["orphaned_delegations"] == 0
    assert stats["top_delegatees"] == []


@pytest.mark.asyncio
async def test_delegation_stats_contract_with_delegations(db_session):
    """Test that delegation stats provider returns complete contract with actual delegations."""
    service = DelegationService(db_session)
    
    # Create test users
    user1 = User(
        email="user1@example.com",
        username="user1",
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    user2 = User(
        email="user2@example.com", 
        username="user2",
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    user3 = User(
        email="user3@example.com",
        username="user3", 
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    
    db_session.add_all([user1, user2, user3])
    await db_session.flush()
    
    # Create a delegation
    delegation = Delegation(
        delegator_id=user1.id,
        delegatee_id=user2.id,
        start_date=datetime.utcnow(),
        end_date=None,
        poll_id=None,
    )
    db_session.add(delegation)
    await db_session.flush()
    
    # Get stats
    stats = await service.get_delegation_stats(poll_id=None)
    
    # Verify all required keys exist
    required_keys = {
        "active_delegations",
        "unique_delegators", 
        "unique_delegatees",
        "avg_chain_length",
        "max_chain_length",
        "cycles_detected",
        "orphaned_delegations",
        "top_delegatees",
        "poll_id"
    }
    
    assert set(stats.keys()) == required_keys, f"Missing keys: {required_keys - set(stats.keys())}"
    
    # Verify correct types
    assert isinstance(stats["active_delegations"], int)
    assert isinstance(stats["unique_delegators"], int)
    assert isinstance(stats["unique_delegatees"], int)
    assert isinstance(stats["avg_chain_length"], float)
    assert isinstance(stats["max_chain_length"], int)
    assert isinstance(stats["cycles_detected"], int)
    assert isinstance(stats["orphaned_delegations"], int)
    assert isinstance(stats["top_delegatees"], list)
    assert stats["poll_id"] is None
    
    # Verify expected values for single delegation
    assert stats["active_delegations"] == 1
    assert stats["unique_delegators"] == 1
    assert stats["unique_delegatees"] == 1
    assert stats["avg_chain_length"] == 0.0  # No chain, just direct delegation
    assert stats["max_chain_length"] == 0
    assert stats["cycles_detected"] == 0
    assert stats["orphaned_delegations"] == 0
    assert len(stats["top_delegatees"]) == 1
    assert isinstance(stats["top_delegatees"][0], tuple)
    assert len(stats["top_delegatees"][0]) == 2
    assert isinstance(stats["top_delegatees"][0][0], str)  # delegatee_id as string
    assert isinstance(stats["top_delegatees"][0][1], int)  # count


@pytest.mark.asyncio
async def test_delegation_stats_contract_top_delegatees_structure(db_session):
    """Test that top_delegatees has the correct structure."""
    service = DelegationService(db_session)
    
    # Create test users
    user1 = User(
        email="user1@example.com",
        username="user1",
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    user2 = User(
        email="user2@example.com",
        username="user2", 
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    
    db_session.add_all([user1, user2])
    await db_session.flush()
    
    # Create multiple delegators
    delegators = []
    for i in range(3):
        u = User(
            email=f"delegator{i}@example.com",
            username=f"delegator{i}",
            hashed_password=get_password_hash("password"),
            is_active=True,
        )
        db_session.add(u)
        delegators.append(u)
    await db_session.flush()
    
    # Create delegations from each delegator to the same delegatee
    for u in delegators:
        db_session.add(Delegation(
            delegator_id=u.id,
            delegatee_id=user2.id,
            start_date=datetime.utcnow(),
            end_date=None,
            poll_id=None,
        ))
    await db_session.flush()
    
    # Get stats
    stats = await service.get_delegation_stats(poll_id=None)
    
    # Verify top_delegatees structure
    assert isinstance(stats["top_delegatees"], list)
    assert len(stats["top_delegatees"]) > 0
    
    for item in stats["top_delegatees"]:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)  # delegatee_id as string
        assert isinstance(item[1], int)  # count
        assert item[1] > 0  # count should be positive


@pytest.mark.asyncio
async def test_delegation_stats_contract_format_stats(db_session):
    """Test that _format_stats method returns complete contract."""
    service = DelegationService(db_session)
    
    # Test with empty stats
    empty_stats = {}
    formatted = service._format_stats(empty_stats)
    
    # Verify all required keys exist
    required_keys = {
        "active_delegations",
        "unique_delegators", 
        "unique_delegatees",
        "avg_chain_length",
        "max_chain_length",
        "cycles_detected",
        "orphaned_delegations",
        "top_delegatees",
        "poll_id"
    }
    
    assert set(formatted.keys()) == required_keys, f"Missing keys: {required_keys - set(formatted.keys())}"
    
    # Verify correct types and default values
    assert isinstance(formatted["active_delegations"], int)
    assert formatted["active_delegations"] == 0
    
    assert isinstance(formatted["unique_delegators"], int)
    assert formatted["unique_delegators"] == 0
    
    assert isinstance(formatted["unique_delegatees"], int)
    assert formatted["unique_delegatees"] == 0
    
    assert isinstance(formatted["avg_chain_length"], float)
    assert formatted["avg_chain_length"] == 0.0
    
    assert isinstance(formatted["max_chain_length"], int)
    assert formatted["max_chain_length"] == 0
    
    assert isinstance(formatted["cycles_detected"], int)
    assert formatted["cycles_detected"] == 0
    
    assert isinstance(formatted["orphaned_delegations"], int)
    assert formatted["orphaned_delegations"] == 0
    
    assert isinstance(formatted["top_delegatees"], list)
    assert formatted["top_delegatees"] == []
    
    assert formatted["poll_id"] is None
    
    # Test with partial stats
    partial_stats = {
        "active_delegations": 5,
        "unique_delegators": 3,
        "poll_id": uuid4()
    }
    formatted = service._format_stats(partial_stats, poll_id=partial_stats["poll_id"])
    
    assert formatted["active_delegations"] == 5
    assert formatted["unique_delegators"] == 3
    assert formatted["unique_delegatees"] == 0  # default
    assert formatted["avg_chain_length"] == 0.0  # default
    assert formatted["poll_id"] == str(partial_stats["poll_id"])
    
    # Test with string values (should be converted)
    stats_with_strings = {
        "active_delegations": "5",
        "unique_delegators": "3",
        "avg_chain_length": "2.5",
        "max_chain_length": "10"
    }
    
    formatted = service._format_stats(stats_with_strings)
    
    # Should convert string values to appropriate types
    assert isinstance(formatted["active_delegations"], int)
    assert formatted["active_delegations"] == 5
    assert isinstance(formatted["unique_delegators"], int)
    assert formatted["unique_delegators"] == 3
    assert isinstance(formatted["avg_chain_length"], float)
    assert formatted["avg_chain_length"] == 2.5
    assert isinstance(formatted["max_chain_length"], int)
    assert formatted["max_chain_length"] == 10


@pytest.mark.asyncio
async def test_delegation_stats_contract_edge_cases(db_session):
    """Test delegation stats provider with edge cases."""
    service = DelegationService(db_session)
    
    # Test with None values in stats
    stats_with_nones = {
        "active_delegations": None,
        "unique_delegators": None,
        "unique_delegatees": None,
        "avg_chain_length": None,
        "max_chain_length": None,
        "cycles_detected": None,
        "orphaned_delegations": None,
        "top_delegatees": None
    }
    
    formatted = service._format_stats(stats_with_nones)
    
    # Should handle None values gracefully
    assert formatted["active_delegations"] == 0
    assert formatted["unique_delegators"] == 0
    assert formatted["unique_delegatees"] == 0
    assert formatted["avg_chain_length"] == 0.0
    assert formatted["max_chain_length"] == 0
    assert formatted["cycles_detected"] == 0
    assert formatted["orphaned_delegations"] == 0
    assert formatted["top_delegatees"] == []
