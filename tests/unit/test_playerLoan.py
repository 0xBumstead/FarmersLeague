from pydoc import plain
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
        _,
        player_loan,
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
        player_loan.listPlayerForLoan(
            1000, Web3.toWei(2, "ether"), token_id, {"from": not_owner}
        )
    # Listing for more than 1,300,000 should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.listPlayerForLoan(
            1400000, Web3.toWei(2, "ether"), token_id, {"from": owner}
        )

    # List for loan the player
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)
    player_id = list_tx.events["listingPlayerForLoan"]["tokenId"]
    duration = list_tx.events["listingPlayerForLoan"]["duration"]
    price = list_tx.events["listingPlayerForLoan"]["price"]

    # Listing a player already listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.listPlayerForLoan(
            1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
        )

    assert player_id == token_id
    assert duration == 1000
    assert price == Web3.toWei(2, "ether")
    assert player_loan.playersForLoan(token_id) == (duration, price)


def test_can_unlist_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        _,
        _,
        player_loan,
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
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id, {"from": owner}
    )
    list_tx.wait(1)

    # Unlisting from an account not owner of the token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.unlistPlayer(token_id, {"from": not_owner})

    # Unlist for loan the player
    unlist_tx = player_loan.unlistPlayer(token_id, {"from": owner})
    unlist_tx.wait(1)
    player_id = unlist_tx.events["unlistingPlayer"]["tokenId"]

    # Unlisting a player not listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.unlistPlayer(token_id, {"from": owner})

    assert player_id == token_id
    assert player_loan.playersForLoan(token_id) == (0, 0)


def test_can_loan_player():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
        _,
        _,
        _,
        _,
        _,
    ) = deploy()
    fund_with_link(
        verifiable_random_footballer.address, owner, None, Web3.toWei(100, "ether")
    )
    # Mint a token that will be listed for loan
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_for_loan = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id_for_loan, {"from": owner}
    )
    list_tx.wait(1)
    # Mint another token that won’t be listed for loan
    request_tx = verifiable_random_footballer.requestPlayer(
        {"from": owner, "value": Web3.toWei(0.1, "ether")}
    )
    request_tx.wait(1)
    request_id = request_tx.events["requestedPlayer"]["requestId"]
    token_id_not_for_loan = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )

    # Approve the transfer of KICK token from the loan contract
    approve_tx = kick_token.approve(
        player_loan.address, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)

    # Loan a player from an account with not enough KICK token should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.loan(token_id_for_loan, {"from": not_owner})

    # Transfer some KICK token to the not_owner account
    transfer_tx = kick_token.transfer(
        not_owner, Web3.toWei(10, "ether"), {"from": owner}
    )
    transfer_tx.wait(1)

    # Loan a player not listed should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.loan(token_id_not_for_loan, {"from": not_owner})

    loan_tx = player_loan.loan(token_id_for_loan, {"from": not_owner})
    loan_tx.wait(1)
    chain = Chain()

    # Loan a player already on loan should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.loan(token_id_for_loan, {"from": not_owner})

    assert player_loan.loans(token_id_for_loan) == (not_owner, len(chain) + 1000 - 2)
    assert kick_token.balanceOf(not_owner) == Web3.toWei(8, "ether")
    assert kick_token.balanceOf(owner) == Web3.toWei(
        99999990 + 2 * 9750 / 10000, "ether"
    ) - Web3.toWei(10000 * 100, "ether")
    assert kick_token.balanceOf(player_loan) == Web3.toWei(2 * 250 / 10000, "ether")
    assert loan_tx.events["loanPlayer"]["tokenId"] == token_id_for_loan
    assert loan_tx.events["loanPlayer"]["borrower"] == not_owner
    assert loan_tx.events["loanPlayer"]["term"] == len(chain) + 1000 - 2


def test_can_withdraw():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        verifiable_random_footballer,
        kick_token,
        _,
        player_loan,
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
    token_id_for_loan = request_tx.events["requestedPlayer"]["tokenId"]
    random_number = 987
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, random_number, verifiable_random_footballer.address
    )
    list_tx = player_loan.listPlayerForLoan(
        1000, Web3.toWei(2, "ether"), token_id_for_loan, {"from": owner}
    )
    list_tx.wait(1)
    approve_tx = kick_token.approve(
        player_loan.address, Web3.toWei(2, "ether"), {"from": not_owner}
    )
    approve_tx.wait(1)
    transfer_tx = kick_token.transfer(
        not_owner, Web3.toWei(10, "ether"), {"from": owner}
    )
    transfer_tx.wait(1)
    loan_tx = player_loan.loan(token_id_for_loan, {"from": not_owner})
    loan_tx.wait(1)

    # Withdrawing from an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.withdraw({"from": not_owner})

    withdraw_tx = player_loan.withdraw({"from": owner})
    withdraw_tx.wait(1)

    assert kick_token.balanceOf(player_loan) == 0
    assert kick_token.balanceOf(owner) == Web3.toWei(99999992, "ether") - Web3.toWei(
        10000 * 100, "ether"
    )


def test_can_set_maximum_duration():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    not_owner = get_account(index=1)
    (
        _,
        _,
        _,
        player_loan,
        _,
        _,
        _,
        _,
        _,
    ) = deploy()

    # Set the price with an account not owner should fail
    with pytest.raises(exceptions.VirtualMachineError):
        player_loan.setMaximumDuration(1500000, {"from": not_owner})

    set_tx = player_loan.setMaximumDuration(1500000, {"from": owner})
    set_tx.wait(1)

    assert (
        player_loan.maximumDuration()
        == set_tx.events["updateMaximumDuration"]["duration"]
    )
    assert player_loan.maximumDuration() == 1500000
