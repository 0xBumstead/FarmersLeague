from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
    fund_with_link,
)
from scripts.deploy import deploy
from brownie import network
import pytest


def test_can_list_two_players():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
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
    # Mint two players (no need to generate metadata here)
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    first_token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    second_token_id = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 789
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Approve and list first player
    approve_tx = verifiable_random_footballer.approve(
        player_transfer.address, first_token_id
    )
    approve_tx.wait(1)
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(2, "ether"), first_token_id, {"from": owner}
    )
    list_tx.wait(1)

    # Approve and list second player
    approve_tx = verifiable_random_footballer.approve(
        player_transfer.address, second_token_id
    )
    approve_tx.wait(1)
    list_tx = player_transfer.listPlayerForTransfer(
        Web3.toWei(3, "ether"), second_token_id, {"from": owner}
    )
    list_tx.wait(1)

    assert player_transfer.getTransferListArray() == (first_token_id, second_token_id)
