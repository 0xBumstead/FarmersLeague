from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from scripts.deploy import deploy
from brownie import network, exceptions
from brownie.network.state import Chain
import pytest


def test_can_list_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    # Get two different accounts
    owner = get_account()
    not_owner = get_account(index=1)
    # Deploy the contracts and fund for ChainLink VRF usage
    (
        verifiable_random_footballer,
        _,
        player_transfer,
        _,
        _,
        _,
        _,
        _,
        _,
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
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Listing from an account not owner of the token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.listPlayerForTransfer(
            Web3.toWei(2, "ether"), token_id, {"from": not_owner}
        )
    # Listing a token not approved should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.listPlayerForTransfer(
            Web3.toWei(2, "ether"), token_id, {"from": owner}
        )

    # List for transfer the player
    approve_tx = verifiable_random_footballer.approve(player_transfer.address, token_id)
    approve_tx.wait(1)
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    player_id = list_tx.events["listingPlayerForTransfer"]["tokenId"]
    price = list_tx.events["listingPlayerForTransfer"]["price"]

    # Listing a player already listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.listPlayerForTransfer(
            Web3.toWei(2, "ether"), token_id, {"from": owner}
        )

    assert player_id == token_id
    assert price == Web3.toWei(2, "ether")
    assert price == player_transfer.playersForTransfer(token_id)
    assert player_transfer.getTransferListArray() == (token_id,)


def test_can_unlist_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        _,
        player_transfer,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = verifiable_random_footballer.approve(player_transfer.address, token_id)
    approve_tx.wait(1)
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)

    # Unlisting from an account not owner of the token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.unlistPlayer(token_id, {"from": not_owner})

    # Unlist for transfer the player
    unlist_tx = player_transfer.unlistPlayer(token_id, {"from": owner})
    unlist_tx.wait(1)
    player_id = unlist_tx.events["unlistingPlayer"]["tokenId"]

    # Unlisting a player not listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.unlistPlayer(token_id, {"from": owner})

    assert player_id == token_id
    assert player_transfer.playersForTransfer(token_id) == 0
    assert player_transfer.getTransferListArray() == (0,)


def test_can_transfer_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        player_transfer,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    # Mint a token that will be listed for transfer
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_for_transfer = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = verifiable_random_footballer.approve(
        player_transfer.address, token_id_for_transfer
    )
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(2, "ether"), token_id_for_transfer, {"from": owner}
    )
    list_tx.wait(1)
    # Mint another token that won’t be listed for transfer
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_not_for_transfer = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 1234
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Approve the transfer of KICK token from the transfer contract
    approve_tx = kick_token.approve(
        player_transfer.address, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)

    # Transfer a player from an account with not enough KICK token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.transfer(token_id_for_transfer, {"from": not_owner})

    # Transfer some KICK token to the not_owner account
    transfer_tx = kick_token.transfer(
        not_owner, Web3.toWei(10, "ether"), {"from": owner}
    )
    transfer_tx.wait(1)

    # Transfer a player not listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.transfer(token_id_not_for_transfer, {"from": not_owner})

    transfer_tx = player_transfer.transfer(token_id_for_transfer, {"from": not_owner})
    transfer_tx.wait(1)

    assert kick_token.balanceOf(not_owner) == Web3.toWei(8, "ether")
    assert kick_token.balanceOf(owner) == Web3.toWei(
        99999990 + 2 * 9750 / 10000, "ether"
    ) - Web3.toWei(10000 * 100, "ether")
    assert kick_token.balanceOf(player_transfer) == Web3.toWei(2 * 250 / 10000, "ether")
    assert transfer_tx.events["unlistingPlayer"]["tokenId"] == token_id_for_transfer
    assert player_transfer.playersForTransfer(token_id_for_transfer) == 0
    assert verifiable_random_footballer.ownerOf(token_id_for_transfer) == not_owner
    assert player_transfer.getTransferListArray() == (0,)


def test_can_withdraw():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        player_transfer,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    approve_tx = verifiable_random_footballer.approve(player_transfer.address, token_id)
    approve_tx.wait(1)
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    approve_tx = kick_token.approve(
        player_transfer.address, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    transfer_tx = kick_token.transfer(
        not_owner, Web3.toWei(10, "ether"), {"from": owner}
    )
    transfer_tx.wait(1)
    transfer_tx = player_transfer.transfer(token_id, {"from": not_owner})
    transfer_tx.wait(1)

    # Withdrawing from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_transfer.withdraw({"from": not_owner})

    withdraw_tx = player_transfer.withdraw({"from": owner})
    withdraw_tx.wait(1)

    assert kick_token.balanceOf(player_transfer) == 0
    assert kick_token.balanceOf(owner) == Web3.toWei(99999992, "ether") - Web3.toWei(
        10000 * 100, "ether"
    )
