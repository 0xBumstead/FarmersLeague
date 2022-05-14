from web3 import Web3
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from scripts.deploy import deploy
from brownie import network, exceptions
from brownie.network.state import Chain


def test_can_claim_token():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    # Get two different accounts
    owner = get_account()
    not_owner = get_account(index=1)
    # Deploy the contracts and fund for ChainLink VRF usage
    (
        verifiable_random_footballer,
        kick_token,
        _,
        _,
        _,
        _,
        _,
        _,
        claim_kick_token,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    # Mint a player (no need to generate metadata here)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    player_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Withdraw all the KICK tokens
    withdraw_tx = claim_kick_token.withdraw({"from": owner})
    withdraw_tx.wait(1)

    # Claiming while the contract has no token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        claim_kick_token.claim(player_id, {"from": owner})

    # Transfer the KICK token back to the contract
    transfer_kick = kick_token.transfer(
        claim_kick_token, Web3.toWei(10000 * 100, "ether"), {"from": owner}
    )
    transfer_kick.wait(1)

    # Claiming from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        claim_kick_token.claim(player_id, {"from": not_owner})

    # Claiming for a non exsting token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        claim_kick_token.claim(2, {"from": owner})

    # Save the balances before the claim
    old_owner_balance = kick_token.balanceOf(owner)
    old_contract_balance = kick_token.balanceOf(claim_kick_token)

    # Claim 100 KICK token
    claim_tx = claim_kick_token.claim(player_id, {"from": owner})
    claim_tx.wait(1)

    assert claim_kick_token.NFTClaim(player_id) == True
    assert kick_token.balanceOf(owner) == old_owner_balance + Web3.toWei(100, "ether")
    assert kick_token.balanceOf(claim_kick_token) == old_contract_balance - Web3.toWei(
        100, "ether"
    )
    assert claim_tx.events["tokenClaimed"]["tokenId"] == player_id


def test_can_withdraw_kick():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        kick_token,
        _,
        _,
        _,
        _,
        _,
        _,
        claim_kick_token,
    ) = deploy()

    # Withdraw from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        claim_kick_token.withdraw({"from": not_owner})

    owner_balance = kick_token.balanceOf(owner)
    withdraw_tx = claim_kick_token.withdraw({"from": owner})
    withdraw_tx.wait(1)

    assert kick_token.balanceOf(owner) == owner_balance + Web3.toWei(
        10000 * 100, "ether"
    )
    assert kick_token.balanceOf(claim_kick_token) == 0
