from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)
from scripts.deploy import deploy
from brownie import network, exceptions
import pytest


def test_can_request_tokenId():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    # Get an account
    owner = get_account()
    # Deploy the contract and fund for ChainLink VRF usage
    (verifiable_random_footballer, _, _, _) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )

    # Request a player
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    token_id = request_tx.events["requestedPlayer"]["tokenId"]

    assert token_id == 1
    # Requesting a token id with a value < 0.1 ETH should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.requestPlayer(
            {"from": owner, "value": Web3.toWei(0.05, "ether")}
        )


def test_can_mint_token():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    (verifiable_random_footballer, _, _, _) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]

    # Mint the player with randomness
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    token_owner = verifiable_random_footballer.ownerOf(token_id)

    assert token_owner == owner.address


def test_can_generate_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (verifiable_random_footballer, _, _, _) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]

    # Generating the metadata for a token id without randomness should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.generatePlayer(token_id, {"from": owner})

    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Generating the metadata from an account not owner of the token id should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.generatePlayer(token_id, {"from": not_owner})

    # Generate the player’s metadata
    generate_tx = verifiable_random_footballer.generatePlayer(token_id, {"from": owner})
    generate_tx.wait(1)

    # Generating 2 times the metadata for the same token id should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.generatePlayer(token_id, {"from": owner})
    # Generating the metadata for a non-minted token id should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.generatePlayer(3, {"from": owner})


def test_can_withdraw():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (verifiable_random_footballer, _, _, _) = deploy()
    fund_with_link(verifiable_random_footballer.address)
    ownerOldBalance = owner.balance()
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": not_owner, "value": Web3.toWei(1, "ether")}
    )
    request_tx.wait(1)

    # Withdrawing the eth sent by the not owner account
    withdraw_tx = verifiable_random_footballer.withdraw({"from": owner})
    withdraw_tx.wait(1)

    # Withdrawing from an account not owner of the contrac should fail
    with pytest.raises(exceptions.VirtualMachineError):
        verifiable_random_footballer.withdraw({"from": not_owner})

    assert owner.balance() == ownerOldBalance + Web3.toWei(1, "ether")
    assert verifiable_random_footballer.balance() == 0
