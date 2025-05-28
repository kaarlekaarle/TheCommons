import pytest
from brownie import accounts, chain, reverts
from utils import get_contract, get_contract_interface
from web3 import Web3


@pytest.fixture(scope="module")
def commons_contract(Commons):
    return Commons.deploy({"from": accounts[0]})


@pytest.fixture(scope="module")
def delegation_contract(Delegation, commons_contract):
    return Delegation.deploy(commons_contract.address, {"from": accounts[0]})


@pytest.fixture(scope="module")
def delegation_interface(delegation_contract):
    return get_contract_interface(delegation_contract)


@pytest.fixture(scope="module")
def commons_interface(commons_contract):
    return get_contract_interface(commons_contract)


def test_multiple_delegations(commons_contract, delegation_contract, commons_interface, delegation_interface):
    # Setup test accounts
    delegator = accounts[0]
    delegate1 = accounts[1]
    delegate2 = accounts[2]
    delegate3 = accounts[3]

    # Initial balances
    initial_balance = commons_interface.balanceOf(delegator)
    assert initial_balance > 0, "Delegator must have tokens"

    # Delegate to first delegate
    delegation_interface.delegate(delegate1, 100, {"from": delegator})

    # Verify first delegation
    delegation1 = delegation_interface.getDelegation(delegator, delegate1)
    assert delegation1[0] == 100  # amount
    assert delegation1[1] == 0    # startTime
    assert delegation1[2] == 0    # endTime

    # Delegate to second delegate
    delegation_interface.delegate(delegate2, 200, {"from": delegator})

    # Verify second delegation
    delegation2 = delegation_interface.getDelegation(delegator, delegate2)
    assert delegation2[0] == 200  # amount
    assert delegation2[1] == 0    # startTime
    assert delegation2[2] == 0    # endTime

    # Delegate to third delegate
    delegation_interface.delegate(delegate3, 300, {"from": delegator})

    # Verify third delegation
    delegation3 = delegation_interface.getDelegation(delegator, delegate3)
    assert delegation3[0] == 300  # amount
    assert delegation3[1] == 0    # startTime
    assert delegation3[2] == 0    # endTime

    # Verify total delegated amount
    total_delegated = delegation_interface.getTotalDelegated(delegator)
    assert total_delegated == 600  # 100 + 200 + 300

    # Verify delegator's remaining balance
    remaining_balance = commons_interface.balanceOf(delegator)
    assert remaining_balance == initial_balance - 600

    # Verify delegate balances
    assert commons_interface.balanceOf(delegate1) == 100
    assert commons_interface.balanceOf(delegate2) == 200
    assert commons_interface.balanceOf(delegate3) == 300


@pytest.mark.asyncio
async def test_create_multiple_delegations():
    """Test creating multiple delegations to different users."""

    # Create test users
    user1 = await create_test_user("user1")
    user2 = await create_test_user("user2")
    user3 = await create_test_user("user3")

    # Create a poll
    poll = await create_test_poll(user1.id)

    # Create delegations
    delegation1 = await create_delegation(user1.id, user2.id, poll.id)
    delegation2 = await create_delegation(user1.id, user3.id, poll.id)

    # Verify delegations
    active_delegations = await get_active_delegations(user1.id)
    assert len(active_delegations) == 2